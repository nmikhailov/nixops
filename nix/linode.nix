# Configuration specific to the Linode backend

{ config, pkgs, ... }:

with pkgs.lib;
{
  ###### interface

  options = {
    deployment.linode = {

      username = mkOption {
        default = "";
        type = types.nullOr types.str;
        description = ''
          Username of the Linode account.

          If left empty, the value of the environment variable
          <envar>LINODE_USER</envar> is used instead.
        '';
      };

      apiKey = mkOption {
        default = "";
        type = types.nullOr types.str;
        description = ''
          Linode APIKEY.

          If left empty, the value of the environment variable
          <envar>LINODE_APIKEY</envar> is used instead.
        '';
      };

      plan = mkOption {
        default = "";
        type = types.str;
        description = ''
          Linode server plan.
        '';
      };

      datacenter = mkOption {
        default = "";
        type = types.str;
        description = ''
          Linode datacenter region.
        '';
      };

      paymentTerm = mkOption {
        default = "1";
        type = types.str;
        description = ''
          Payment term.
        '';
      };

    }; 
  };

  ###### implementation

  config = mkIf (config.deployment.targetEnv == "linode") {
    nixpkgs.system = mkOverride 900 "x86_64-linux";
    boot.loader.grub.version = 2;
    boot.loader.grub.timeout = 1;
    services.openssh.enable = true;

    # Blacklist nvidiafb by default as it causes issues with some GPUs.
    boot.blacklistedKernelModules = [ "nvidiafb" ];

    security.initialRootPassword = mkDefault "!";
  };
}
