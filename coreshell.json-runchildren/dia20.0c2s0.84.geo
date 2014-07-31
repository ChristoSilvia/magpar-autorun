algebraic3d
solid core = cylinder (0,0,-1;0,0,1;8.4)
         and plane (0,0,20.0;0,0,1)
         and plane (0,0,-20.0;0,0,-1) -maxh=1.5;

solid shell = cylinder (0,0,-1;0,0,1;10.0)
         and plane (0,0,20.0;0,0,1)
         and plane (0,0,-20.0;0,0,-1)
         and not core -maxh=1.5;

tlo core;
tlo shell;