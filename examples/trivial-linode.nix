{
  machine =
    { 
      imports = [ ./linode-info.nix ];
      
      deployment.targetEnv = "linode";
      deployment.linode.region = "london";
      deployment.linode.instanceType = "Linode 2048";
    };
}
