# Pin a prebuilt binary from a GitHub release, for use in any shell.nix:
#
#   pkgs.installFromGithub {
#     repo    = "gruntwork-io/terragrunt";
#     version = "0.77.22";
#     asset   = "terragrunt_linux_amd64";
#     hash    = "sha256-QgNlhiUPXbU90kYEJ8XfQ0IPoiuTWZjxUwGBR09SU4Y=";
#   }
#
# `hash` is always the hash of the asset as downloaded, archive or not:
#
#   nix hash convert --to sri --hash-algo sha256 "$(nix-prefetch-url <url>)"
#
# Only reachable from impure eval (`nix-shell`, `import <nixpkgs> {}`); a pure
# flake never reads ~/.config/nixpkgs/overlays. Keep it out of shared repos.

final: prev:

let
  inherit (final) lib;
  archiveSuffixes = [ ".zip" ".tar.gz" ".tgz" ".tar.xz" ".tar.bz2" ".tar.zst" ];
in
{
  installFromGithub =
    { repo
    , version
    , asset
    , hash
    , tag ? "v${version}"
    , pname ? lib.last (lib.splitString "/" repo)
    , binaries ? [ pname ]
    }:
    let
      isArchive = lib.any (s: lib.hasSuffix s asset) archiveSuffixes;
      url = "https://github.com/${repo}/releases/download/${tag}/${asset}";
    in
    final.stdenvNoCC.mkDerivation ({
      inherit pname version;

      src = final.fetchurl { inherit url hash; };

      dontUnpack = !isArchive;
      nativeBuildInputs = lib.optional (lib.hasSuffix ".zip" asset) final.unzip;

      installPhase = ''
        runHook preInstall
      ''
      + (
        if isArchive
        then lib.concatMapStrings (b: ''
          install -Dm755 "$(find . -type f -name ${lib.escapeShellArg b} | head -n1)" "$out/bin/${b}"
        '') binaries
        else ''
          install -Dm755 $src "$out/bin/${lib.head binaries}"
        ''
      )
      + ''
        runHook postInstall
      '';

      meta.mainProgram = lib.head binaries;
    }
    # Release archives are inconsistent about wrapping their payload in a
    # versioned root dir, so unpack in place and find the binaries instead.
    // lib.optionalAttrs isArchive { sourceRoot = "."; });
}
