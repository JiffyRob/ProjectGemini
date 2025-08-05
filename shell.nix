{ pkgs ? import <nixpkgs> {} }:

(pkgs.buildFHSEnv {
  name = "simple-x11-env";
  targetPkgs = pkgs: (with pkgs; [
    udev
    alsa-lib
    python312
    python312Packages.pygame-ce
    python312Packages.numpy
    python312Packages.pip
    python312Packages.virtualenv
    libglvnd
    glib
    vscode

  ]) ++ (with pkgs.xorg; [
    libX11
    libXcursor
    libXrandr
  ]);
  multiPkgs = pkgs: (with pkgs; [
    udev
    alsa-lib
  ]);
  # runScript = ./wrapped_run.sh;
}).env
