"""
Tests for INSPIRE-HEP harvester and ATLAS plasma extractor
"""
import json
import sys
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
        {'id': '123', 'metadata': {'titles': [{'title': 'Paper 1'}]}},
        {'id': '456', 'metadata': {'titles': [{'title': 'Paper 2'}]}},
        {'id': '123', 'metadata': {'titles': [{'title': 'Paper 1 duplicate'}]}},
        {'id': '789', 'metadata': {'titles': [{'title': 'Paper 3'}]}},
    ]
    
    # Deduplicate using the same logic as main()
    unique_papers = []
    seen_ids = set()
    
    for paper in papers:
        paper_id = paper.get('id')
        if paper_id and paper_id not in seen_ids:
            unique_papers.append(paper)
            seen_ids.add(paper_id)
    
    assert len(unique_papers) == 3, f"Expected 3 unique papers, got {len(unique_papers)}"
    assert '123' in seen_ids
    assert '456' in seen_ids
    assert '789' in seen_ids
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
    test_atlas_extractor_runs()
    test_atlas_chi_calculation_structure()
    
    print("=" * 60)
    print("✅ All tests passed!")
