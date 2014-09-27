{
  machine =
    { 
      imports = [ ./linode-info.nix ];
      
      deployment.targetEnv = "linode";
      deployment.linode.datacenter = "london";
      deployment.linode.plan = "Linode 1024";
    };
}
