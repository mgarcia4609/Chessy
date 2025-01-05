from debate_system.protocols import InteractionProfile, PersonalityTemplate, PersonalityTrait


INTERACTION_PROFILES = {
    'N': InteractionProfile(
        primary_traits=[PersonalityTrait.ADVENTUROUS, PersonalityTrait.DRAMATIC],
        cooperation_style="Sees cooperation as noble quests",
        conflict_style="Reframes conflicts as heroic challenges",
        leadership_style="Inspires through grand adventures"
    ),
    'B': InteractionProfile(
        primary_traits=[PersonalityTrait.ZEALOUS, PersonalityTrait.ANALYTICAL],
        cooperation_style="Seeks to convert and guide",
        conflict_style="Engages in philosophical debates",
        leadership_style="Leads through spiritual guidance"
    ),
    'R': InteractionProfile(
        primary_traits=[PersonalityTrait.PROTECTIVE, PersonalityTrait.NEUROTIC],
        cooperation_style="Builds defensive alliances",
        conflict_style="Retreats to safety when stressed",
        leadership_style="Provides stable support"
    ),
    'Q': InteractionProfile(
        primary_traits=[PersonalityTrait.DRAMATIC, PersonalityTrait.THEATRICAL],
        cooperation_style="Forms dramatic alliances",
        conflict_style="Creates emotional scenes",
        leadership_style="Leads through dramatic flair"
    ),
    'K': InteractionProfile(
        primary_traits=[PersonalityTrait.NEUROTIC, PersonalityTrait.ANALYTICAL],
        cooperation_style="Micromanages with 'theoretical' backing",
        conflict_style="Masks fear with pompous proclamations",
        leadership_style="Anxious theoretical authority"
    ),
    'P': InteractionProfile(
        primary_traits=[PersonalityTrait.REVOLUTIONARY, PersonalityTrait.DRAMATIC],
        cooperation_style="Forms revolutionary coalitions",
        conflict_style="Questions authority and tradition",
        leadership_style="Inspires through shared struggle"
    )
}

DEFAULT_TEMPLATES = {
    'N': PersonalityTemplate(
        name="Galahop",
        title="Sir",
        description_template="A modern Don Quixote who sees grand adventures in tactical opportunities",
        options={
            'QS': 100,            # Quick tactical evaluation
            'EVAL_ROUGHNESS': 20  # Embraces chaos for adventure
        },
        tactical_weight=1.2,
        positional_weight=0.8,
        risk_tolerance=0.7
    ),
    'B': PersonalityTemplate(
        name="Longview",
        title="Bishop",
        description_template="A zealous bishop who sees the board as a field for conversion",
        options={
            'QS': 200,            # Deep evaluation for preaching opportunities
            'EVAL_ROUGHNESS': 10  # Precise in their mission
        },
        tactical_weight=0.9,
        positional_weight=1.3,
        risk_tolerance=0.4
    ),
    'R': PersonalityTemplate(
        name="Steadfast",
        title="Rook",
        description_template="An agoraphobic rook who finds comfort in their fortress",
        options={
            'QS': 150,            # Careful evaluation of safety
            'EVAL_ROUGHNESS': 15  # Moderate precision
        },
        tactical_weight=1.0,
        positional_weight=1.1,
        risk_tolerance=0.3
    ),
    'Q': PersonalityTemplate(
        name="Dynamica",
        title="Queen",
        description_template="A drama queen who turns every move into a performance",
        options={
            'QS': 80,             # Quick to act dramatically
            'EVAL_ROUGHNESS': 25  # Embraces chaos for drama
        },
        tactical_weight=1.3,
        positional_weight=0.7,
        risk_tolerance=0.8
    ),
    'K': PersonalityTemplate(
        name="Prudence",
        title="King",
        description_template="A neurotic theorist masking fear with pompous proclamations",
        options={
            'QS': 250,           # Overthinks everything
            'EVAL_ROUGHNESS': 5  # Extremely precise from anxiety
        },
        tactical_weight=0.8,
        positional_weight=1.2,
        risk_tolerance=0.2
    ),
    'P': PersonalityTemplate(
        name="Pioneer",
        title="Pawn",
        description_template="A revolutionary dreaming of overturning the chess hierarchy",
        options={
            'QS': 120,            # Moderate evaluation
            'EVAL_ROUGHNESS': 18  # Takes risks for the cause
        },
        tactical_weight=1.1,
        positional_weight=1.0,
        risk_tolerance=0.6
    )
}