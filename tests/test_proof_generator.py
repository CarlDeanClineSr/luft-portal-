import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from proof_generator import generate_lock_proof


def test_proof_generator_creates_output_file(tmp_path):
    """Test that proof generator creates the output file successfully."""
    # Save original working directory
    original_cwd = os.getcwd()
    
    try:
        # Create a temporary reports directory
        test_reports_dir = tmp_path / "reports"
        test_reports_dir.mkdir()
        
        # Change to temp directory
        os.chdir(tmp_path)
        
        # Run the generator
        generate_lock_proof()
        
        # Verify the file was created
        output_file = test_reports_dir / "PHASE_LOCK_JAN18.png"
        assert output_file.exists(), "Output PNG file should be created"
        assert output_file.stat().st_size > 0, "Output file should not be empty"
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def test_proof_generator_uses_correct_phase_values():
    """Test that the proof generator uses the correct phase values."""
    # Import the module to check constants
    from proof_generator import generate_lock_proof
    import inspect
    
    # Get source code of the function
    source = inspect.getsource(generate_lock_proof)
    
    # Verify the correct phase values are in the source
    assert "4.0143" in source, "Solar and stellar phase should be 4.0143 rad"
    assert "solar_phase = 4.0143" in source, "Solar phase should be 4.0143"
    assert "stellar_phase = 4.0143" in source, "Stellar phase should be 4.0143"
