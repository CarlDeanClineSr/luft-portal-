"""
Tests for INSPIRE-HEP harvester and ATLAS plasma extractor
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

import harvest_inspire
import atlas_plasma_extractor


def test_inspire_paper_deduplication():
    """Test that duplicate papers are removed correctly"""
    
    # Mock papers with duplicates
    papers = [
        {'id': '123', 'metadata': {'control_number': 1001, 'titles': [{'title': 'Paper 1'}]}},
        {'id': '456', 'metadata': {'control_number': 1002, 'titles': [{'title': 'Paper 2'}]}},
        {'id': '123', 'metadata': {'control_number': 1001, 'titles': [{'title': 'Paper 1 duplicate'}]}},
        {'id': '789', 'metadata': {'control_number': 1003, 'titles': [{'title': 'Paper 3'}]}},
    ]
    
    # Deduplicate using the same logic as main()
    unique_papers = []
    seen_ids = set()
    
    for paper in papers:
        paper_id = harvest_inspire.get_paper_key(paper)
        if paper_id and paper_id not in seen_ids:
            unique_papers.append(paper)
            seen_ids.add(paper_id)
    
    assert len(unique_papers) == 3, f"Expected 3 unique papers, got {len(unique_papers)}"
    assert '1001' in seen_ids
    assert '1002' in seen_ids
    assert '1003' in seen_ids
    print("✓ INSPIRE paper deduplication test passed")


def test_inspire_fetch_with_mock():
    """Test INSPIRE API call with mocked response"""
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'hits': {
            'hits': [
                {'id': '1', 'metadata': {'titles': [{'title': 'Test Paper'}]}}
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    
    with patch('harvest_inspire.requests.get', return_value=mock_response):
        papers = harvest_inspire.fetch_inspire_papers("test query", max_results=1)
        assert len(papers) == 1
        assert papers[0]['id'] == '1'
    
    print("✓ INSPIRE fetch mock test passed")


def test_inspire_relevance_scoring():
    """Test that relevance scoring favors recent, detailed papers."""
    old_paper_age_days = 4000
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recent_paper = {
        'created': now.isoformat(),
        'metadata': {
            'authors': [{'full_name': 'A. Researcher'}],
            'abstracts': [{'value': 'A' * 400}],
            'citation_count': 25,
        }
    }
    older_paper = {
        'created': (now - timedelta(days=old_paper_age_days)).isoformat(),
        'metadata': {
            'authors': [{'full_name': 'B. Author'}],
            'abstracts': [{'value': 'Short'}],
            'citation_count': 0,
        }
    }

    recent_score = harvest_inspire.calculate_relevance_score(recent_paper, reference_time=now)
    older_score = harvest_inspire.calculate_relevance_score(older_paper, reference_time=now)

    assert recent_score > older_score, "Recent paper should score higher than older paper"
    print("✓ INSPIRE relevance scoring test passed")


def test_inspire_parse_created_date():
    """Test created date parsing for valid and invalid inputs."""
    assert harvest_inspire.parse_created_date(None) is None
    assert harvest_inspire.parse_created_date("not-a-date") is None

    parsed = harvest_inspire.parse_created_date("2025-01-01T00:00:00Z")
    assert parsed is not None
    assert parsed.tzinfo is not None

    parsed_naive = harvest_inspire.parse_created_date("2025-01-01T00:00:00")
    assert parsed_naive is not None
    assert parsed_naive.tzinfo is not None
    print("✓ INSPIRE created date parsing test passed")


def test_inspire_paper_key_fallback():
    """Test deduplication key fallback when control_number is missing."""
    paper_with_control = {'id': '999', 'metadata': {'control_number': 42}}
    paper_with_id = {'id': 'abc', 'metadata': {}}
    paper_missing = {'metadata': {}}

    assert harvest_inspire.get_paper_key(paper_with_control) == "42"
    assert harvest_inspire.get_paper_key(paper_with_id) == "abc"
    assert harvest_inspire.get_paper_key(paper_missing) is None
    print("✓ INSPIRE paper key fallback test passed")


def test_atlas_extractor_runs():
    """Test that ATLAS extractor runs without errors"""
    
    # The extractor should run and return 0
    result = atlas_plasma_extractor.main()
    assert result == 0, f"ATLAS extractor should return 0, got {result}"
    print("✓ ATLAS extractor run test passed")


def test_atlas_chi_calculation_structure():
    """Test that χ calculation functions exist"""
    
    # Check that the functions are defined
    assert hasattr(atlas_plasma_extractor, 'calculate_chi_from_atlas')
    assert hasattr(atlas_plasma_extractor, 'analyze_quark_gluon_plasma')
    
    # Test with empty data
    empty_data = []
    chi_values = atlas_plasma_extractor.calculate_chi_from_atlas(empty_data)
    assert chi_values == [], "Empty data should return empty chi values"
    
    qgp_values = atlas_plasma_extractor.analyze_quark_gluon_plasma(empty_data)
    assert qgp_values == [], "Empty data should return empty QGP values"
    
    print("✓ ATLAS χ calculation structure test passed")


if __name__ == '__main__':
    print("Running INSPIRE and ATLAS tool tests...")
    print("=" * 60)
    
    test_inspire_paper_deduplication()
    test_inspire_fetch_with_mock()
    test_inspire_relevance_scoring()
    test_inspire_parse_created_date()
    test_inspire_paper_key_fallback()
    test_atlas_extractor_runs()
    test_atlas_chi_calculation_structure()
    
    print("=" * 60)
    print("✅ All tests passed!")
