import pytest
from piece_agents.personality_factory import PersonalityFactory
from piece_agents.personality_defaults import DEFAULT_TEMPLATES, INTERACTION_PROFILES
from debate_system.protocols import PersonalityTemplate, PersonalityTrait

@pytest.fixture
def factory():
    """Create a fresh personality factory for each test"""
    return PersonalityFactory()

def test_create_personality(factory):
    """Test creating a single personality"""
    # Test knight personality
    knight = factory.create_personality('N')
    assert knight.name == "Sir Galahop"
    assert "modern Don Quixote" in knight.description
    assert knight.tactical_weight == 1.2
    assert knight.positional_weight == 0.8
    assert knight.risk_tolerance == 0.7
    assert knight.options['QS'] == 100
    assert knight.options['EVAL_ROUGHNESS'] == 20

    # Test with index
    knight2 = factory.create_personality('N', index=1)
    assert knight2.name == "Sir Galahop 2"
    assert knight2.tactical_weight == knight.tactical_weight

def test_create_all_personalities(factory):
    """Test creating all personalities"""
    personalities = factory.create_all_personalities()
    
    # Check all piece types are present
    assert set(personalities.keys()) == {'N', 'B', 'R', 'Q', 'K', 'P'}
    
    # Check specific traits of each piece
    assert "modern Don Quixote" in personalities['N'].description
    assert "zealous bishop" in personalities['B'].description
    assert "agoraphobic" in personalities['R'].description
    assert "drama queen" in personalities['Q'].description
    assert "neurotic theorist" in personalities['K'].description
    assert "revolutionary" in personalities['P'].description

def test_create_themed_personality(factory):
    """Test creating themed personalities"""
    # Test aggressive knight
    aggressive = factory.create_themed_personality('N', 'aggressive')
    assert aggressive.tactical_weight > DEFAULT_TEMPLATES['N'].tactical_weight
    assert aggressive.risk_tolerance > DEFAULT_TEMPLATES['N'].risk_tolerance
    assert "aggressively" in aggressive.description.lower()

    # Test defensive bishop
    defensive = factory.create_themed_personality('B', 'defensive')
    assert defensive.positional_weight > DEFAULT_TEMPLATES['B'].positional_weight
    assert defensive.risk_tolerance < DEFAULT_TEMPLATES['B'].risk_tolerance
    assert "defensive" in defensive.description.lower()

    # Test creative queen
    creative = factory.create_themed_personality('Q', 'creative')
    assert creative.tactical_weight > DEFAULT_TEMPLATES['Q'].tactical_weight
    assert creative.positional_weight > DEFAULT_TEMPLATES['Q'].positional_weight
    assert "creative" in creative.description.lower()

def test_invalid_piece_type(factory):
    """Test error handling for invalid piece types"""
    with pytest.raises(ValueError):
        factory.create_personality('X')

def test_custom_templates(factory):
    """Test factory with custom templates"""
    custom_templates = DEFAULT_TEMPLATES.copy()
    custom_templates['N'] = PersonalityTemplate(
        name="CustomKnight",
        title=custom_templates['N'].title,
        description_template=custom_templates['N'].description_template,
        options=custom_templates['N'].options,
        tactical_weight=2.0,
        positional_weight=1.0,
        risk_tolerance=0.5
    )
    
    custom_factory = PersonalityFactory(templates=custom_templates)
    personality = custom_factory.create_personality('N')
    
    assert personality.tactical_weight == 2.0
    assert "CustomKnight" in personality.name

def test_personality_traits_integration(factory):
    """Test that personality traits properly influence themed variations"""
    # Test dramatic queen gets appropriate themed descriptions
    queen = factory.create_themed_personality('Q', 'aggressive')
    assert PersonalityTrait.DRAMATIC in INTERACTION_PROFILES['Q'].primary_traits
    assert "dramatic" in queen.description.lower()

    # Test zealous bishop gets appropriate themed descriptions
    bishop = factory.create_themed_personality('B', 'aggressive')
    assert PersonalityTrait.ZEALOUS in INTERACTION_PROFILES['B'].primary_traits
    assert "zealously" in bishop.description.lower()

    # Test protective rook gets appropriate themed descriptions
    rook = factory.create_themed_personality('R', 'defensive')
    assert PersonalityTrait.PROTECTIVE in INTERACTION_PROFILES['R'].primary_traits
    assert "ultra-defensive" in rook.description.lower() 