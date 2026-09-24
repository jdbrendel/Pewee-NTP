import openmc
import math
import numpy as np


#################################
# # # ~ ~ ~ MATERIALS ~ ~ ~ # # #
#################################

# 9 Control drums
# M1 elements (graphite) replace partial fuel cells, except 12 total of halves (2 per 60 degree slice)
fuel = openmc.Material(1, "fuel")

fuel.add_nuclide('U235', 0.93)
fuel.add_nuclide('U238', 0.07)
fuel.add_element('C', 30)
fuel.set_density('g/cm3', 2.2)

graphite = openmc.Material(2, "graphite")
graphite.add_element('C', 1.0)
graphite.set_density('g/cm3', 1.8)

beryl= openmc.Material(3, "beryllium Reflector")
beryl.add_element("Be", 1.0)
beryl.set_density("g/cm3", 1.848)

zirconium = openmc.Material(4, "zirconium")
zirconium.add_element('Zr', 1.0)
zirconium.set_density('g/cm3', 6.6)

prop = openmc.Material(5, "prop")
prop.add_nuclide('H1', 2.0)
prop.set_density('g/cm3', 0.071)

nbc = openmc.Material(6, "niobium_carbide")     # This might be supposed to be ZrC for Pewee specifically
nbc.add_element('Nb', 1.0)
nbc.add_element('C', 1.0)
nbc.set_density('g/cm3', 7.8)

'''
ss = openmc.Material(7, "stainless_steel")
ss.add_element('Fe', 0.7)
ss.add_element('Cr', 0.19)
ss.add_element('Ni', 0.10)
ss.add_element('Mn', 0.01)
ss.set_density('g/cm3', 8.0)
'''

ZrH = openmc.Material(7, 'Zirconium Hydride') #Unclear if ZrH or ZrH2 appropriate
ZrH.add_element('Zr', .5)
ZrH.add_element('H', .5)
ZrH.set_density('g/cm3', 5.9)

poison = openmc.Material(8, 'Neutron Poison')
poison.add_nuclide('B10', 4.0)
poison.add_element('C', 1.0)
poison.set_density('g/cm3', 2.52)

inconel = openmc.Material(9, 'Inconel-718')
inconel.add_element('B', 0.000267)
inconel.add_element('C', 0.003507)
inconel.add_element('Al', 0.010694)
inconel.add_element('Si', 0.006534)
inconel.add_element('P', 0.000261)
inconel.add_element('S', 0.000252)
inconel.add_element('Ti', 0.010850)
inconel.add_element('Cr', 0.210871)
inconel.add_element('Mn', 0.003340)
inconel.add_element('Fe', 0.175671)
inconel.add_element('Ni', 0.516184)
inconel.add_element('Co', 0.008911)
inconel.add_element('Cu', 0.002479)
inconel.add_element('Nb', 0.031833)
inconel.add_element('Mo', 0.018346)
inconel.set_density('g/cm3', 8.190000)

ZrC = openmc.Material(10, 'Zirconium Carbide')
ZrC.add_element('Zr', .5)
ZrC.add_element('C', .5)
ZrC.set_density('g/cm3', 6.63)

materials = openmc.Materials((fuel, graphite, beryl, zirconium, prop, nbc, ZrH, poison, inconel, ZrC))
materials.export_to_xml()


####################################
# # # ~ ~ ~ FUEL ELEMENT ~ ~ ~ # # #
####################################

t_nbc = 0.0254  # cm
r_pin = openmc.ZCylinder(r=0.279/2) # cm

r_inner = openmc.ZCylinder(r=r_pin.r)
r_outer = openmc.ZCylinder(r=r_pin.r + t_nbc)

fuel_cell = openmc.Cell(fill=fuel, region=+r_outer)
ZrC_cell = openmc.Cell(fill=ZrC, region=+r_inner & -r_outer)
prop_cell = openmc.Cell(fill=prop, region=-r_inner)
pin_universe = openmc.Universe(cells=(fuel_cell, ZrC_cell, prop_cell))

all_carbon_cell = openmc.Cell(fill=graphite)
excess_cell = openmc.Cell(fill=fuel)

outer_universe = openmc.Universe(cells=(excess_cell,))
graphite_universe = openmc.Universe(cells = (all_carbon_cell,))

cell_edge_length = 1.1045
pitch = 3/8 * cell_edge_length

lattice19 = openmc.HexLattice()

lattice19.center = (0., 0.)
lattice19.pitch = (pitch,)
lattice19.outer = outer_universe

ring_1 = [pin_universe]*12
ring_2 = [pin_universe]*6
ring_3 = [pin_universe]
lattice19.universes = [ring_1, ring_2, ring_3]
lattice19.orientation = 'x'

hex_orientation = 'x'
reactor_bottom = 0.0
reactor_height = 160
reactor_top = reactor_bottom + reactor_height
axial_coords = np.linspace(reactor_bottom, reactor_top)

# create additional axial regions
axial_planes = [openmc.ZPlane(z0=coord) for coord in axial_coords]
# axial planes
min_z = axial_planes[0]
min_z.boundary_type = 'vacuum'
max_z = axial_planes[-1]
max_z.boundary_type = 'vacuum'


big_hex = openmc.model.HexagonalPrism(edge_length = cell_edge_length, orientation='x', boundary_type='periodic')

outer_hex = big_hex
inner_hex = openmc.model.HexagonalPrism(edge_length = cell_edge_length - t_nbc, orientation='x', boundary_type='periodic')

fuel_region_cell = openmc.Cell(fill=lattice19, region=-inner_hex & +min_z & -max_z)

outer_ZrC_cell = openmc.Cell(fill=ZrC, region=+inner_hex & -outer_hex & +min_z & -max_z)

# fuel_element_cell = openmc.Cell(fill=lattice19, region=-big_hex & +min_z & -max_z)
fuel_element_universe = openmc.Universe(cells=[fuel_region_cell, outer_ZrC_cell])

xz_plane = openmc.YPlane(y0=0.0)
fuel_12_Cell = openmc.Cell(fill=lattice19, region=-inner_hex & -xz_plane & +min_z & -max_z)
ZrC_12_Cell = openmc.Cell(fill=ZrC, region=+inner_hex & -xz_plane & -outer_hex & +min_z & -max_z)
graphite_cell = openmc.Cell(fill = graphite_universe, region = -big_hex & +xz_plane & +min_z & -max_z)

fuel_12_universe = openmc.Universe(cells=[fuel_12_Cell, ZrC_12_Cell, graphite_cell])

cell_12_hole_element2 = openmc.Cell(fill = fuel_12_universe, region = -outer_hex & +min_z & -max_z)
cell_12_hole_element2.rotation = (0, 0, -60)
universe_12_hole_element2 = openmc.Universe(cells = [cell_12_hole_element2])

cell_12_hole_element3 = openmc.Cell(fill = fuel_12_universe, region = -outer_hex & +min_z & -max_z)
cell_12_hole_element3.rotation = (0, 0, -120)
universe_12_hole_element3 = openmc.Universe(cells = [cell_12_hole_element3])

cell_12_hole_element4 = openmc.Cell(fill = fuel_12_universe, region = -outer_hex & +min_z & -max_z)
cell_12_hole_element4.rotation = (0, 0, -180)
universe_12_hole_element4 = openmc.Universe(cells = [cell_12_hole_element4])

cell_12_hole_element5 = openmc.Cell(fill = fuel_12_universe, region = -outer_hex & +min_z & -max_z)
cell_12_hole_element5.rotation = (0, 0, -240)
universe_12_hole_element5 = openmc.Universe(cells = [cell_12_hole_element5])

cell_12_hole_element6 = openmc.Cell(fill = fuel_12_universe, region = -outer_hex & +min_z & -max_z)
cell_12_hole_element6.rotation = (0, 0, -300)
universe_12_hole_element6 = openmc.Universe(cells = [cell_12_hole_element6])

#######################################
# # # ~ ~ ~ SUPPORT ELEMENT ~ ~ ~ # # #
#######################################


ann_thick = .15

#THICKNESS OF BOTH COOLANT FLOW CHANNELS IN SUPPORT = .2 CM IN THICKNESS, TOTAL AREA = 1/2 SS PIN AREA

innertubeor = .521/2 #cm
innertubeir = innertubeor - .051
#rinnerprop = innertubeir - .013

innertube_inner_r=openmc.ZCylinder(r=innertubeir)
innertube_outer_r=openmc.ZCylinder(r=innertubeor)

ZrH_inner_r = openmc.ZCylinder(r=.533/2)
ZrH_outer_r = openmc.ZCylinder(r=1.168/2)

outertube_inner_r = openmc.ZCylinder(r=1.397/2-.0205)
outertube_outer_r = openmc.ZCylinder(r=1.397/2)

ZrC_inner_r = openmc.ZCylinder(r=1.410/2)
ZrC_outer_r = openmc.ZCylinder(r=1.613/2)

graphite_inner_r = openmc.ZCylinder(r=1.613/2+.013)

centerprop_cell = openmc.Cell(fill = prop, region = -innertube_inner_r | +ZrH_outer_r & -outertube_inner_r)

tietube_cell = openmc.Cell(fill = inconel, region = -innertube_outer_r & +innertube_inner_r | -outertube_outer_r & +outertube_inner_r)

ZrH_cell = openmc.Cell(fill = ZrH, region = -ZrH_outer_r & +ZrH_inner_r)







support_cell = openmc.Cell(fill=graphite, region=-inner_hex & +min_z & -max_z & +graphite_inner_r)
support_ZrC_cell = openmc.Cell(fill=ZrC, region=+inner_hex & -outer_hex & +min_z & -max_z | -ZrC_outer_r & +ZrC_inner_r)
support_universe = openmc.Universe(cells=[support_cell, support_ZrC_cell, centerprop_cell, tietube_cell, ZrH_cell])











assembly_lattice = openmc.HexLattice()
assembly_lattice.center = (0., 0.)
assembly_lattice.pitch = (cell_edge_length*np.sqrt(3),)
#assembly_lattice.orientation = 'x'
#assembly_lattice.outer = fuel_element_universe
assembly_lattice.outer = graphite_universe
rings = 16

universes = []

for ring in range(rings, 0, -1):
    ring_univs = []
    for pos in range(6*ring):
        
        if (ring == 14):
            ring_univs.append(graphite_universe)
        elif (pos in [2, 76]) and (ring == 13):
            ring_univs.append(fuel_12_universe)
                
        elif (pos in [11, 15]) and (ring == 13):
            ring_univs.append(universe_12_hole_element2)
        elif (pos in [24, 28]) and (ring == 13):
            ring_univs.append(universe_12_hole_element3)
        elif (pos in [37, 41]) and (ring == 13):
            ring_univs.append(universe_12_hole_element4)
        elif (pos in [50, 54]) and (ring == 13):
            ring_univs.append(universe_12_hole_element5)
        elif (pos in [63, 67]) and (ring == 13):
            ring_univs.append(universe_12_hole_element6)


        elif (pos in [1, 12, 14, 25, 27, 38, 40, 51, 53, 64, 66, 77]) and (ring == 13):
            ring_univs.append(graphite_universe)
        elif (ring == 13):
            ring_univs.append(fuel_element_universe)
        elif (pos % 2 == 0) and (ring % 2 == 0):
            ring_univs.append(support_universe)
        #elif (pos % 1 == 0) and (ring == 13):
        #    ring_univs.append(support_universe)
        else:
            ring_univs.append(fuel_element_universe)
        
    
    universes.append(ring_univs)

universes.append([support_universe])

assembly_lattice.universes = universes

'''
ring1 = [fuel_element_universe]*6
center = [support_universe]

assembly_lattice.universes = [ring1, center]
'''


# # # Dodecahedrom Bounding # # #

s_edge = 8 * cell_edge_length
r_flat = 12.5 * np.sqrt(3) * cell_edge_length
r_vertex = np.sqrt(r_flat**2 + (s_edge / 2)**2)
theta_vertex = np.arctan((s_edge / 2) / r_flat)
r_corner = r_vertex * np.cos(np.radians(30) - theta_vertex)

# Array to hold the bounding half-spaces of the dodecagon
planes = []

# Define planes for the 6 short edges
for i in range(6):
    angle = np.radians(60 * i+30)
    A = np.cos(angle)
    B = np.sin(angle)
    # Surface equation: A*x + B*y - r_flat = 0
    p = openmc.Plane(a=A, b=B, c=0.0, d=r_flat)
    planes.append(-p)  # Keep the interior region (negative half-space)

# Define planes for the 6 connecting long edges
for i in range(6):
    angle = np.radians(60 * i )
    A = np.cos(angle)
    B = np.sin(angle)
    p = openmc.Plane(a=A, b=B, c=0.0, d=r_corner)
    planes.append(-p)

# Intersect all 12 plane half-spaces to form the solid dodecagon region
assembly_dodec = planes[0]
for p in planes[1:]:
    assembly_dodec &= p

# Apply boundary conditions to all outer surfaces
for p in planes:
    # Extract the surface object from the half-space expression
    p.surface.boundary_type = 'vacuum'

dodec_2d = planes[0]
for p in planes[1:]:
    dodec_2d &= p


#Alt
r_reactor = 53/2 # cm
r_Graphite_Shell = openmc.Cylinder(r=r_reactor)
Graphite_Shell_Cell = openmc.Cell(fill = graphite, region = -r_Graphite_Shell & ~dodec_2d & +min_z & -max_z)


# # # Control Drums # # #

r_ref = 46.5 # Placed here for inconvenience

# Angle of control drums: (0 = absorber completely facing core)
theta_cd = 0

cd_r = 5 # [cm] (half of 10)

drum_cylinder = openmc.ZCylinder(r=cd_r)

tan_60 = np.tan(np.radians(60))
plane_plus_60 = openmc.Plane(a=tan_60, b=-1.0, c=0.0, d=0.0, name="Plane +60 deg")
plane_minus_60 = openmc.Plane(a=tan_60, b=1.0, c=0.0, d=0.0, name="Plane -60 deg")

poison_region = -drum_cylinder & +plane_plus_60 & +plane_minus_60

reflector_region = -drum_cylinder & (~poison_region)

poison_cell = openmc.Cell(fill=poison, region=poison_region)
d_reflector_cell = openmc.Cell(fill=beryl, region=reflector_region)

drum_universe = openmc.Universe(cells=[poison_cell, d_reflector_cell])

ring_r = r_ref - 7.5
drums = 9
angle_step = 360/drums

drums_universe = openmc.Universe(name="Control Drum Ring")

all_drum_regions = []

for i in range(drums):
    angle_deg = i * angle_step + 90
    angle_rad = math.radians(angle_deg)

    x = ring_r * math.cos(angle_rad)
    y = ring_r * math.sin(angle_rad)

    rotation_z = angle_deg + 180.0 + theta_cd

    #translated_drum_cyl = openmc.ZCylinder(x0=x, y0=y, r=cd_r)
    #all_drum_regions.append(-translated_drum_cyl)

    global_drum_region = -drum_cylinder.translate((x, y, 0.0))
    all_drum_regions.append(global_drum_region)

    # Instantiate Cell, then assign fill, translation, and rotation via properties
    drum_cell = openmc.Cell(name=f"drum_cell_{i}")   
    drum_cell.fill = drum_universe
    drum_cell.region = global_drum_region
    drum_cell.translation = (x, y, 0.0)
    drum_cell.rotation = (0.0, 0.0, rotation_z)

    drums_universe.add_cell(drum_cell)


drums_combined_region = all_drum_regions[0]
for reg in all_drum_regions[1:]:
    drums_combined_region |= reg

# # # Reflector # # #

# r_ref = 46.5 # cm (core radius .53/2 + .2 m reflector thickness = .465 m = 46.5 cm )
r_reflector = openmc.ZCylinder(r=r_ref)
reflector_cell = openmc.Cell(fill=beryl, region=+r_Graphite_Shell & -r_reflector & ~drums_combined_region)

# Assembling Fuel into Dodecahedron
assembly_cell = openmc.Cell(fill=assembly_lattice,
                            region=assembly_dodec & +min_z & -max_z)

drums_cell = openmc.Cell(fill=drums_universe,
                         region=drums_combined_region & +min_z & -max_z)

reactor_universe = openmc.Universe(cells=[assembly_cell, reflector_cell, drums_cell, Graphite_Shell_Cell])

geometry = openmc.Geometry(reactor_universe)
geometry.export_to_xml()


mcolors = {
    prop: 'blue',
    fuel: 'green',
    graphite: 'grey',
    ZrC: 'black',
    #ZrH: 
    #ss: 'yellow',
    poison: 'darkviolet',
    beryl: 'teal',
    inconel: 'yellow'
}

#XY Cross Section
plot1 = openmc.Plot()
plot1.filename = 'Core_Loading_CS_xy'
plot1.origin = (0, 0, reactor_height/2)
plot1.width = (100, 100)
plot1.pixels = (8000, 8000)
plot1.color_by = 'material'
plot1.colors = mcolors

plots1 = openmc.Plots([plot1])
plots1.export_to_xml()

openmc.plot_geometry()


all_drums_universe = openmc.Universe(cells=[drums_cell])
drumgeometry = openmc.Geometry(all_drums_universe)
drumgeometry.export_to_xml()


plot2 = openmc.Plot()
plot2.filename = 'Drums in the Deep'
plot2.width    = (100, 100)
plot2.origin   = (0.0, 0.0, reactor_height/2.0)
plot2.pixels   = (6000, 6000)
plot2.color_by = 'material'
plot2.colors   = mcolors

'''
#XZ Cross Section
plot2 = openmc.Plot()
plot2.filename = 'Fuel_Pin_CS_xz'
plot2.width    = (6*cell_edge_length, 1.5*reactor_height)
plot2.basis    = 'xz'
plot2.origin   = (0.0, 0.0, reactor_height/2.0)
plot2.pixels   = (5000,40000)
plot2.color_by = 'material'
plot2.colors   = mcolors
'''

'''
#YZ Cross Section
plot3 = openmc.Plot()
plot3.filename = 'Fuel_Pin_CS_yz'
plot3.width    = (6*cell_edge_length, 1.5*reactor_height)
plot3.basis    = 'yz'
plot3.origin   = (0.0, 0.0, reactor_height/2.0)
plot3.pixels   = (5000,40000)
plot3.color_by = 'material'
plot3.colors   = mcolors
'''


'''
#XY Cross Section Cell Color
plot4 = openmc.Plot()
plot4.filename = 'Core_Loading_CS_xy_CellColor'
plot4.origin = (0, 0, reactor_height/2)
plot4.width = (100, 100)
plot4.pixels = (5000, 5000)
plot4.color_by = 'cell'
'''
#plots = openmc.Plots([plot1, plot2, plot3, plot4])
plots2 = openmc.Plots([plot2])
plots2.export_to_xml()

openmc.plot_geometry()
