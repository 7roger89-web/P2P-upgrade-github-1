import os
import json
import shutil
import subprocess
import sys

REPO = "/home/ubuntu/fw01_work/auth-f01"
TEST_ROOT = "/tmp/p2p_installer_anomaly_test"
ARTIFACT_PATH = os.path.join(REPO, "reports/candidates/P2P-8.4.7-C-codex.46-full-distribution-candidate.zip")
ARTIFACT_SHA = "2901adca106d3533b3df37e1d10d8a375162b64b001c32bec28b4b178c2f3bb7"

def setup_fixture(project_path):
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    os.makedirs(project_path)
    # Create a dummy file to simulate an existing project
    with open(os.path.join(project_path, "README.md"), "w") as f:
        f.write("# Dummy Project")

def run_installer(project_path, version="8.4.7-C-codex.46"):
    cmd = [
        "python3", 
        os.path.join(REPO, "scripts/p2p_safe_installer.py"),
        "install",
        project_path,
        ARTIFACT_PATH,
        "--sha", ARTIFACT_SHA,
        "--version", version
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_anomaly_1_identity_mismatch():
    print("Test Anomaly 1: Identity Mismatch Detection...")
    # Artifact .46 reportedly has VERSION=.41 internally.
    # We expect the installer to block this if we request .46 but find .41.
    setup_fixture(TEST_ROOT)
    
    # We know .46 artifact has internal VERSION=8.4.7-C-codex.41
    # Requesting .46 should fail if identity validation is working.
    code, out, err = run_installer(TEST_ROOT, version="8.4.7-C-codex.46")
    
    print(f"  Installer Return Code: {code}")
    if code != 0:
        print(f"  PASS: Installer blocked mismatch. Error: {err.strip()}")
        assert "PACKAGE_VERSION_IDENTITY_MISMATCH" in out or "PACKAGE_VERSION_IDENTITY_MISMATCH" in err
    else:
        print("  FAIL: Installer accepted mismatched identity!")
        assert False, "Installer should have blocked the mismatch"

def test_anomaly_2_doctor_unhealthy_gate():
    print("Test Anomaly 2: Doctor Unhealthy Gate...")
    # In this test environment, doctor will likely be UNHEALTHY because
    # the environment is not a full P2P runtime.
    # We want to ensure project-pin.json reflects this.
    setup_fixture(TEST_ROOT)
    
    # Bypass Anomaly 1 check by requesting .41 (which is what VERSION says)
    code, out, err = run_installer(TEST_ROOT, version="8.4.7-C-codex.41")
    
    pin_path = os.path.join(TEST_ROOT, ".p2p", "project-pin.json")
    if os.path.exists(pin_path):
        with open(pin_path) as f:
            pin = json.load(f)
        print(f"  Doctor Result in Pin: {pin.get('doctor_result')}")
        print(f"  Installation Status in Pin: {pin.get('installation_status')}")
        
        if pin.get('doctor_result') != "HEALTHY":
            assert pin.get('verification_status') == "INSTALLED_UNVERIFIED"
            print("  PASS: UNHEALTHY doctor resulted in INSTALLED_UNVERIFIED")
        else:
            print(f"  Note: Doctor was {pin.get('doctor_result')}")
    else:
        print(f"  ERROR: Installer output: {out} {err}")
        assert False, "project-pin.json not created"

if __name__ == "__main__":
    try:
        test_anomaly_1_identity_mismatch()
        print("")
        test_anomaly_2_doctor_unhealthy_gate()
        print("\nALL ANOMALY REPRODUCTION TESTS COMPLETED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
