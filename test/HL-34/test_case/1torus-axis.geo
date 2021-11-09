//-----------------------------------------------------------------------------
// Parameters

h = 5e-3;
rint = 75e-3;  // m
rext = 100.2e-3; // m 
z1 = 25e-3;  // m

rinfty = 3*(rext+rint+z1); // m

//-----------------------------------------------------------------------------
// Definition of points

// Origin
Point(0) = {0,0,0,h};

// Conductor
Point(1) = {rint, -z1, 0, 0.5*h};
Point(2) = {rext, -z1, 0, 0.5*h};
Point(3) = {rext, z1, 0, 0.5*h};
Point(4) = {rint, z1, 0, 0.5*h};

// Air
Point(5) = {0, -rinfty, 0, 20*h};
Point(6) = {0, -1/3*(z1+rinfty), 0, 0.5*h};
Point(7) = {0, 1/3*(z1+rinfty), 0, 0.5*h};
Point(8) = {0, rinfty, 0, 20*h};

//-----------------------------------------------------------------------------
// Definition of line

// Conductor
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};

// Air
Circle(5) = {5, 0, 8};
Line(6) = {8, 7};
Line(7) = {7, 6};
Line(8) = {6, 5};

//-----------------------------------------------------------------------------
// Definition of surface

// Conductor
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

// Air
Curve Loop(2) = {5, 6, 7, 8};
Plane Surface(2) = {2, 1};

//-----------------------------------------------------------------------------
// Definition of physical groups

// Conductor
Physical Curve("Bottom") = {1};
Physical Curve("Exterior") = {2};
Physical Curve("Upper") = {3};
Physical Curve("Interior") = {4};
Physical Surface("Conductor") = {1};

// Air
Physical Curve("Infty") = {5};
Physical Curve("ZAxis") = {6, 7, 8};
Physical Surface("Air") = {2};