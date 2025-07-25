{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "python-env";

  buildInputs = [
    pkgs.python312
    pkgs.python312Packages.pip
  ];

  shellHook = ''
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONUNBUFFERED=1
    python3 -m venv .venv
    source .venv/bin/activate
    # Install requirements if needed
    if [ -f requirements.txt ]; then
      pip install --upgrade pip
      pip install -r requirements.txt
    fi
  '';
}
