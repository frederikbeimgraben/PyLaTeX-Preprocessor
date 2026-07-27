{
  description = "PyTeX-Preprocessor — type-safe LaTeX document generation with Python";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      python = pkgs.python313;

      pytex-preprocessor = python.pkgs.buildPythonApplication {
        pname = "pytex-preprocessor";
        version = "1.0.6";
        pyproject = true;

        src = ./.;

        build-system = [ python.pkgs.setuptools ];
        dependencies = with python.pkgs; [ pydantic marko ];

        # The test suite needs Python 3.14 t-string syntax and an external
        # tectonic and biber toolchain. The sandboxed build has neither, so it
        # skips the tests. Run the full suite with `pytest` in the devShell.
        doCheck = false;

        pythonImportsCheck = [ "pytex" "pytex_builder" ];

        meta = {
          description = "Type-safe LaTeX document generation with Python";
          homepage = "https://github.com/frederikbeimgraben/PyTeX-Preprocessor";
          license = pkgs.lib.licenses.gpl3Plus;
          mainProgram = "pytex";
        };
      };
    in
    {
      packages.${system} = {
        default = pytex-preprocessor;
        pytex-preprocessor = pytex-preprocessor;
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = [
          (python.withPackages (ps: with ps; [ pydantic marko pytest ]))
          pkgs.ruff
          pkgs.basedpyright
        ];

        shellHook = ''
          echo "PyTeX-Preprocessor dev shell — python ${python.version}, ruff, basedpyright, pytest"
          echo "Install the package editable with: pip install -e . (in a venv) — or use the provided interpreter."
          # Start the interactive zsh of the user, which loads ~/.zshrc. The
          # guard keeps `nix develop -c <cmd>` and other non-interactive uses
          # in bash.
          [[ $- == *i* ]] && exec ${pkgs.zsh}/bin/zsh
        '';
      };
    };
}
