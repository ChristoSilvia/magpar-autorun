algebraic3d
solid core = cylinder (0,0,-1;0,0,1;12.6)
         and plane (0,0,30.0;0,0,1)
         and plane (0,0,-30.0;0,0,-1) -maxh=1.5;

solid shell = cylinder (0,0,-1;0,0,1;15.0)
         and plane (0,0,30.0;0,0,1)
         and plane (0,0,-30.0;0,0,-1)
         and not core -maxh=1.5;

tlo core;
tlo shell;