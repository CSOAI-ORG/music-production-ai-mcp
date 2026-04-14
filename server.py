"""
Music Production AI MCP Server
Audio and music tools powered by MEOK AI Labs.
"""

import time
import re
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("music-production-ai-mcp")

_call_counts: dict[str, list[float]] = defaultdict(list)
FREE_TIER_LIMIT = 30
WINDOW = 86400


def _check_rate_limit(tool_name: str) -> None:
    now = time.time()
    _call_counts[tool_name] = [t for t in _call_counts[tool_name] if now - t < WINDOW]
    if len(_call_counts[tool_name]) >= FREE_TIER_LIMIT:
        raise ValueError(f"Rate limit exceeded for {tool_name}. Free tier: {FREE_TIER_LIMIT}/day.")
    _call_counts[tool_name].append(now)


NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_IDX = {n: i for i, n in enumerate(NOTES)}

# Enharmonic aliases
ENHARMONIC = {"Db": "C#", "Eb": "D#", "Fb": "E", "Gb": "F#", "Ab": "G#", "Bb": "A#", "Cb": "B",
              "E#": "F", "B#": "C"}

SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "blues": [0, 3, 5, 6, 7, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
}

CHORD_FORMULAS = {
    "major": [0, 4, 7], "minor": [0, 3, 7], "dim": [0, 3, 6], "aug": [0, 4, 8],
    "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "dom7": [0, 4, 7, 10],
    "dim7": [0, 3, 6, 9], "sus2": [0, 2, 7], "sus4": [0, 5, 7],
    "add9": [0, 4, 7, 14], "min9": [0, 3, 7, 10, 14],
}

PROGRESSIONS = {
    "pop": [("I", "major"), ("V", "major"), ("vi", "minor"), ("IV", "major")],
    "blues": [("I", "dom7"), ("I", "dom7"), ("I", "dom7"), ("I", "dom7"),
              ("IV", "dom7"), ("IV", "dom7"), ("I", "dom7"), ("I", "dom7"),
              ("V", "dom7"), ("IV", "dom7"), ("I", "dom7"), ("V", "dom7")],
    "jazz_ii_v_i": [("ii", "min7"), ("V", "dom7"), ("I", "maj7")],
    "sad": [("vi", "minor"), ("IV", "major"), ("I", "major"), ("V", "major")],
    "epic": [("I", "major"), ("III", "major"), ("IV", "major"), ("vi", "minor")],
    "rock": [("I", "major"), ("bVII", "major"), ("IV", "major"), ("I", "major")],
    "rnb": [("I", "maj7"), ("vi", "min7"), ("ii", "min7"), ("V", "dom7")],
}

ROMAN_TO_DEGREE = {"I": 0, "ii": 2, "II": 2, "bIII": 3, "III": 4, "iii": 4, "IV": 5, "iv": 5,
                   "V": 7, "v": 7, "vi": 8, "VI": 9, "bVII": 10, "VII": 11, "vii": 11}


def _normalize_note(note: str) -> str:
    note = note.strip()
    if len(note) > 1:
        note = note[0].upper() + note[1:]
    else:
        note = note.upper()
    return ENHARMONIC.get(note, note)


def _get_note(root_idx: int, interval: int) -> str:
    return NOTES[(root_idx + interval) % 12]


@mcp.tool()
def generate_chord_progression(
    key: str = "C",
    scale: str = "major",
    style: str = "pop",
    bars: int = 4,
    include_voicings: bool = True) -> dict:
    """Generate a chord progression in a given key and style.

    Args:
        key: Root note (e.g. C, F#, Bb)
        scale: Scale type: major, minor, dorian, mixolydian
        style: Progression style: pop, blues, jazz_ii_v_i, sad, epic, rock, rnb
        bars: Number of bars (repeats the progression to fill)
        include_voicings: Include note spellings for each chord
    """
    _check_rate_limit("generate_chord_progression")

    root = _normalize_note(key)
    root_idx = NOTE_TO_IDX.get(root, 0)

    progression_template = PROGRESSIONS.get(style, PROGRESSIONS["pop"])

    chords = []
    for bar in range(bars):
        template = progression_template[bar % len(progression_template)]
        numeral, quality = template
        degree = ROMAN_TO_DEGREE.get(numeral, 0)
        chord_root = _get_note(root_idx, degree)
        formula = CHORD_FORMULAS.get(quality, CHORD_FORMULAS["major"])

        chord_root_idx = NOTE_TO_IDX[chord_root]
        notes = [_get_note(chord_root_idx, interval) for interval in formula]

        chord_name = f"{chord_root}{'' if quality == 'major' else 'm' if quality == 'minor' else quality}"

        entry = {
            "bar": bar + 1,
            "numeral": numeral,
            "chord": chord_name,
        }
        if include_voicings:
            entry["notes"] = notes

        chords.append(entry)

    return {
        "key": root,
        "scale": scale,
        "style": style,
        "total_bars": bars,
        "progression": chords,
        "suggested_tempo": {
            "pop": "100-130 BPM", "blues": "60-100 BPM", "jazz_ii_v_i": "80-160 BPM",
            "sad": "60-90 BPM", "epic": "70-100 BPM", "rock": "110-150 BPM", "rnb": "70-100 BPM",
        }.get(style, "80-120 BPM"),
    }


@mcp.tool()
def detect_tempo(
    beat_timestamps: list[float]) -> dict:
    """Detect tempo (BPM) from beat timestamps.

    Args:
        beat_timestamps: List of beat occurrence times in seconds (must have at least 4 beats)
    """
    _check_rate_limit("detect_tempo")

    if len(beat_timestamps) < 4:
        return {"error": "Need at least 4 beat timestamps for reliable tempo detection"}

    timestamps = sorted(beat_timestamps)
    intervals = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]

    # Filter outliers (remove intervals > 2x or < 0.5x the median)
    sorted_intervals = sorted(intervals)
    median = sorted_intervals[len(sorted_intervals) // 2]
    filtered = [i for i in intervals if 0.5 * median <= i <= 2.0 * median]

    if not filtered:
        filtered = intervals

    avg_interval = sum(filtered) / len(filtered)
    bpm = 60.0 / avg_interval

    # Snap to common tempos if close
    common_tempos = [60, 70, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 128, 130, 135, 140, 145, 150, 160, 170, 174, 180]
    nearest = min(common_tempos, key=lambda t: abs(t - bpm))

    # Confidence based on interval consistency
    if filtered:
        variance = sum((i - avg_interval) ** 2 for i in filtered) / len(filtered)
        std_dev = variance ** 0.5
        consistency = max(0, 1 - (std_dev / avg_interval))
    else:
        consistency = 0

    # Detect time signature hint
    if bpm > 150:
        time_sig_hint = "Possibly 3/4 or fast 4/4"
    elif 55 < bpm < 75:
        time_sig_hint = "Possibly 6/8 or slow 4/4"
    else:
        time_sig_hint = "Likely 4/4"

    return {
        "detected_bpm": round(bpm, 1),
        "nearest_common_bpm": nearest,
        "confidence": f"{consistency * 100:.0f}%",
        "beat_count": len(timestamps),
        "average_interval_sec": round(avg_interval, 4),
        "time_signature_hint": time_sig_hint,
        "ms_per_beat": round(avg_interval * 1000, 1),
        "samples_per_beat_44100": round(avg_interval * 44100),
    }


@mcp.tool()
def find_key(
    notes: list[str],
    prioritize_major: bool = True) -> dict:
    """Detect the musical key from a set of notes.

    Args:
        notes: List of note names found in the piece (e.g. ["C", "E", "G", "A", "D"])
        prioritize_major: Prefer major keys when scores are tied
    """
    _check_rate_limit("find_key")

    normalized = [_normalize_note(n) for n in notes]
    note_set = set(normalized)

    results = []
    for root_name in NOTES:
        root_idx = NOTE_TO_IDX[root_name]
        for scale_name, intervals in SCALE_INTERVALS.items():
            if scale_name.startswith("pentatonic") or scale_name == "blues":
                continue
            scale_notes = set(_get_note(root_idx, i) for i in intervals)
            matching = note_set & scale_notes
            missing = note_set - scale_notes
            score = len(matching) / len(note_set) if note_set else 0

            results.append({
                "key": f"{root_name} {scale_name}",
                "root": root_name,
                "scale": scale_name,
                "matching_notes": sorted(matching),
                "non_matching_notes": sorted(missing),
                "match_score": round(score * 100, 1),
                "scale_notes": [_get_note(root_idx, i) for i in intervals],
            })

    # Sort by score, then prefer major if tied
    results.sort(key=lambda r: (-r["match_score"], 0 if (r["scale"] == "major" and prioritize_major) else 1))

    top_results = results[:5]

    return {
        "input_notes": sorted(note_set),
        "best_match": top_results[0] if top_results else None,
        "alternatives": top_results[1:],
        "note_count": len(note_set),
    }


@mcp.tool()
def analyze_lyrics(
    lyrics: str,
    title: str = "") -> dict:
    """Analyze song lyrics for structure, rhyme scheme, syllable count, and themes.

    Args:
        lyrics: Full song lyrics text
        title: Song title (optional)
    """
    _check_rate_limit("analyze_lyrics")

    lines = [l.strip() for l in lyrics.strip().split("\n") if l.strip()]
    words = lyrics.lower().split()
    word_count = len(words)

    # Detect sections
    section_markers = {"verse": 0, "chorus": 0, "bridge": 0, "pre-chorus": 0, "intro": 0, "outro": 0, "hook": 0}
    for line in lines:
        lower = line.lower().strip("[]() ")
        for marker in section_markers:
            if marker in lower:
                section_markers[marker] += 1

    # Count unique words
    clean_words = [re.sub(r'[^\w]', '', w) for w in words]
    clean_words = [w for w in clean_words if w]
    unique_words = set(clean_words)
    lexical_diversity = len(unique_words) / len(clean_words) if clean_words else 0

    # Find repeated phrases (potential hooks/choruses)
    line_counts = defaultdict(int)
    for line in lines:
        normalized = re.sub(r'[^\w\s]', '', line.lower()).strip()
        if len(normalized) > 5:
            line_counts[normalized] += 1

    repeated_lines = {line: count for line, count in line_counts.items() if count > 1}

    # Simple rhyme detection (last word ending)
    def get_ending(word):
        w = re.sub(r'[^\w]', '', word.lower())
        return w[-3:] if len(w) >= 3 else w

    rhyme_pairs = []
    for i in range(len(lines) - 1):
        w1 = lines[i].split()
        w2 = lines[i + 1].split()
        if w1 and w2:
            if get_ending(w1[-1]) == get_ending(w2[-1]) and w1[-1].lower() != w2[-1].lower():
                rhyme_pairs.append((lines[i][-30:], lines[i + 1][-30:]))

    # Syllable estimate (rough: count vowel groups)
    def count_syllables(text):
        return len(re.findall(r'[aeiouy]+', text.lower()))

    avg_syllables = sum(count_syllables(l) for l in lines) / len(lines) if lines else 0

    # Emotion keywords
    emotions = {
        "love": ["love", "heart", "kiss", "hold", "baby", "darling", "forever"],
        "sadness": ["cry", "tears", "pain", "hurt", "broken", "alone", "lost", "miss"],
        "joy": ["happy", "smile", "laugh", "dance", "celebrate", "shine", "bright"],
        "anger": ["hate", "rage", "fire", "burn", "fight", "scream", "destroy"],
        "hope": ["hope", "dream", "believe", "rise", "light", "tomorrow", "faith"],
    }

    detected_emotions = {}
    for emotion, keywords in emotions.items():
        count = sum(1 for w in clean_words if w in keywords)
        if count > 0:
            detected_emotions[emotion] = count

    return {
        "title": title or "Untitled",
        "statistics": {
            "total_lines": len(lines),
            "word_count": word_count,
            "unique_words": len(unique_words),
            "lexical_diversity": f"{lexical_diversity:.2f}",
            "avg_syllables_per_line": round(avg_syllables, 1),
        },
        "structure": {
            "detected_sections": {k: v for k, v in section_markers.items() if v > 0},
            "repeated_lines": dict(sorted(repeated_lines.items(), key=lambda x: -x[1])[:5]),
        },
        "rhyme_pairs_found": len(rhyme_pairs),
        "sample_rhymes": rhyme_pairs[:5],
        "emotional_tone": detected_emotions,
        "dominant_emotion": max(detected_emotions, key=detected_emotions.get) if detected_emotions else "neutral",
    }


@mcp.tool()
def mixing_recommendations(
    tracks: list[dict],
    genre: str = "pop",
    master_loudness_lufs: float = -14.0) -> dict:
    """Get mixing and mastering recommendations for a multitrack session.

    Args:
        tracks: List of dicts with keys: name, type (vocals, drums, bass, guitar, keys, strings, synth, fx), current_db (optional)
        genre: Genre: pop, rock, hip_hop, electronic, jazz, classical, rnb
        master_loudness_lufs: Target loudness in LUFS (Spotify: -14, Apple: -16, YouTube: -14)
    """
    _check_rate_limit("mixing_recommendations")

    # Genre-specific level guides (relative to master, in dB)
    genre_levels = {
        "pop": {"vocals": -3, "drums": -6, "bass": -8, "guitar": -10, "keys": -12, "strings": -14, "synth": -10, "fx": -18},
        "rock": {"vocals": -4, "drums": -4, "bass": -6, "guitar": -6, "keys": -14, "strings": -16, "synth": -12, "fx": -18},
        "hip_hop": {"vocals": -2, "drums": -4, "bass": -5, "guitar": -14, "keys": -12, "synth": -8, "fx": -16, "strings": -16},
        "electronic": {"vocals": -6, "drums": -3, "bass": -4, "guitar": -16, "keys": -8, "synth": -5, "fx": -12, "strings": -14},
        "jazz": {"vocals": -4, "drums": -8, "bass": -6, "guitar": -8, "keys": -6, "strings": -10, "synth": -16, "fx": -20},
        "classical": {"vocals": -6, "drums": -14, "bass": -10, "guitar": -10, "keys": -8, "strings": -4, "synth": -18, "fx": -16},
        "rnb": {"vocals": -2, "drums": -5, "bass": -5, "guitar": -12, "keys": -8, "synth": -10, "fx": -16, "strings": -14},
    }

    levels = genre_levels.get(genre, genre_levels["pop"])

    eq_guides = {
        "vocals": {"low_cut": "80-120Hz", "presence": "boost 2-4kHz by 2-3dB", "air": "shelf boost 10kHz+", "mud_cut": "cut 200-400Hz if boxy"},
        "drums": {"low_cut": "30Hz", "kick_body": "60-100Hz", "snare_crack": "2-4kHz", "hi_hat": "8-12kHz", "overhead_air": "shelf 12kHz+"},
        "bass": {"low_cut": "30Hz", "body": "60-100Hz", "mid_growl": "800Hz-1.2kHz for presence", "high_cut": "5-8kHz"},
        "guitar": {"low_cut": "80-120Hz", "body": "200-400Hz", "presence": "2-5kHz", "high_cut": "10-12kHz for electric"},
        "keys": {"low_cut": "100-200Hz", "body": "300-500Hz", "clarity": "2-4kHz", "air": "8kHz+"},
        "synth": {"depends_on_sound": True, "low_cut": "varies", "resonance": "1-3kHz can be harsh - cut if needed"},
        "strings": {"low_cut": "80-150Hz", "warmth": "200-400Hz", "presence": "2-4kHz", "air": "8kHz+"},
    }

    compression_guides = {
        "vocals": {"ratio": "3:1 - 4:1", "attack": "10-30ms", "release": "40-80ms", "gain_reduction": "3-6dB"},
        "drums": {"ratio": "4:1 - 8:1", "attack": "1-10ms (fast for control, slow for punch)", "release": "50-100ms"},
        "bass": {"ratio": "4:1 - 6:1", "attack": "10-30ms", "release": "40-80ms"},
        "guitar": {"ratio": "2:1 - 4:1", "attack": "10-25ms", "release": "50-100ms"},
        "keys": {"ratio": "2:1 - 3:1", "attack": "15-30ms", "release": "60-100ms"},
    }

    track_recommendations = []
    for track in tracks:
        track_type = track.get("type", "other").lower()
        name = track.get("name", track_type)
        current = track.get("current_db")

        target_level = levels.get(track_type, -12)
        rec = {
            "track": name,
            "type": track_type,
            "recommended_level_db": target_level,
        }

        if current is not None:
            adjustment = target_level - current
            rec["current_db"] = current
            rec["adjustment"] = f"{'+' if adjustment > 0 else ''}{adjustment:.1f}dB"

        if track_type in eq_guides:
            rec["eq_guide"] = eq_guides[track_type]
        if track_type in compression_guides:
            rec["compression"] = compression_guides[track_type]

        # Panning suggestions
        pan_map = {
            "vocals": "Center", "bass": "Center", "drums": "Center (overheads: L30-R30)",
            "guitar": "L20-L40 or R20-R40", "keys": "L15-R15", "strings": "L30-R30 (wide)",
            "synth": "Varies - automate for movement",
        }
        rec["pan_suggestion"] = pan_map.get(track_type, "Place in stereo field as needed")

        track_recommendations.append(rec)

    return {
        "genre": genre,
        "target_loudness": f"{master_loudness_lufs} LUFS",
        "track_count": len(tracks),
        "track_recommendations": track_recommendations,
        "master_chain": [
            "EQ: gentle low cut at 30Hz, slight high shelf boost",
            "Multiband compression: control low end, gentle glue",
            "Stereo imaging: check mono compatibility",
            f"Limiter: target {master_loudness_lufs} LUFS integrated",
        ],
        "reference_loudness": {
            "Spotify": "-14 LUFS",
            "Apple Music": "-16 LUFS",
            "YouTube": "-14 LUFS",
            "CD": "-9 to -12 LUFS",
        },
    }


if __name__ == "__main__":
    mcp.run()
