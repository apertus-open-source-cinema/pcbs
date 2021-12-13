{ pkgs ? import <nixpkgs> { }
, pkgsLinux ? import <nixpkgs> { system = "x86_64-linux"; }
}:
let
  pcb-tools = pkgs.python39.pkgs.buildPythonPackage rec {
    pname = "pcb-tools";
    version = "0.1.6";

    src = pkgs.python39.pkgs.fetchPypi {
      inherit pname version;
      sha256 = "0w86la4l9wk0as5n9z26pnfrvg705gwf13k2b0prl2snf6m2avrr";
    };

    propagatedBuildInputs = [
      pkgsLinux.python39Packages.cairocffi
    ];

    preBuild = ''
    substituteInPlace setup.py \
      --replace "0.6" "1.2"
    '';
    meta = with pkgs.lib; {
      description = "Tools to handle Gerber and Excellon files in Python";
      homepage = "https://github.com/curtacircuitos/pcb-tools";
      license = licenses.asl20;
    };
  };
in
  pkgs.dockerTools.streamLayeredImage {
    name = "apertushq/eagle-docker";
    contents = with pkgsLinux; [
      bashInteractive
      eagle7
      xvfb-run
      xdotool
      coreutils
      (python39.withPackages (ps: with ps; [
        scikitimage
        pyquery
        pikepdf
        pcb-tools
      ]))
    ];
    config = {
      Cmd = [ "${pkgsLinux.bashInteractive}/bin/bash" ];
    };
  }
