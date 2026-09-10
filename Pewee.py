import openmc
import math
import numpy as np


#################################
# # # ~ ~ ~ MATERIALS ~ ~ ~ # # #
#################################

# Fuel should be more like TRISO, approx for now
# 9 Control drums
fuel = openmc.Material(1, "fuel")

fuel.add_nuclide('U235', 0.93)
fuel.add_nuclide('U238', 0.07)
fuel.add_element('C', 30)
fuel.set_density('g/cm3', 2.2)

graphite = openmc.Material(2, "graphite")
graphite.add_element('C', 1.0)
graphite.set_density('g/cm3', 1.8)

zirconium = openmc.Material(3, "zirconium")
zirconium.add_element('Zr', 1.0)
zirconium.set_density('g/cm3', 6.6)

prop = openmc.Material(4, "prop")
prop.add_nuclide('H1', 2.0)
prop.set_density('g/cm3', 0.071)

nbc = openmc.Material(5, "niobium_carbide")     # This might be supposed to be ZrC for Pewee specifically
nbc.add_element('Nb', 1.0)
nbc.add_element('C', 1.0)
nbc.set_density('g/cm3', 7.8)

ss = openmc.Material(6, "stainless_steel")
ss.add_element('Fe', 0.7)
ss.add_element('Cr', 0.19)
ss.add_element('Ni', 0.10)
ss.add_element('Mn', 0.01)
ss.set_density('g/cm3', 8.0)



materials = openmc.Materials((fuel, graphite, zirconium, prop, nbc, ss))
materials.export_to_xml()


####################################
# # # ~ ~ ~ FUEL ELEMENT ~ ~ ~ # # #
####################################

t_nbc = 0.0254  # cm
r_pin = openmc.ZCylinder(r=0.279/2) # cm

r_inner = openmc.ZCylinder(r=r_pin.r)
r_outer = openmc.ZCylinder(r=r_pin.r + t_nbc)

fuel_cell = openmc.Cell(fill=fuel, region=+r_outer)
nbc_cell = openmc.Cell(fill=nbc, region=+r_inner & -r_outer)
prop_cell = openmc.Cell(fill=prop, region=-r_inner)
pin_universe = openmc.Universe(cells=(fuel_cell, nbc_cell, prop_cell))

all_carbon_cell = openmc.Cell(fill=graphite)
excess_cell = openmc.Cell(fill=fuel)

outer_universe = openmc.Universe(cells=(excess_cell,))
graphite_universe = openmc.Universe(cells = (all_carbon_cell,))

cell_edge_length = 1.31
pitch = 1/3 * cell_edge_length

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

outer_nbc_cell = openmc.Cell(fill=nbc, region=+inner_hex & -outer_hex & +min_z & -max_z)

# fuel_element_cell = openmc.Cell(fill=lattice19, region=-big_hex & +min_z & -max_z)
fuel_element_universe = openmc.Universe(cells=[fuel_region_cell, outer_nbc_cell])


#######################################
# # # ~ ~ ~ SUPPORT ELEMENT ~ ~ ~ # # #
#######################################


r_support_pin = openmc.ZCylinder(r=0.544/2)

ss_cell = openmc.Cell(fill = ss, region = -r_support_pin)

ann_thick = .15

#THICKNESS OF BOTH COOLANT FLOW CHANNELS IN SUPPORT = .2 CM IN THICKNESS, TOTAL AREA = 1/2 SS PIN AREA
r_inann_in = openmc.ZCylinder(r=0.547)
r_innann_out = openmc.ZCylinder(r=.547 + ann_thick)
r_outann_in = openmc.ZCylinder(r=.547 + .2)
r_outann_out = openmc.ZCylinder(r=.547 + 3*ann_thick)

sup_prop_cell = openmc.Cell(fill=prop, region= (+r_inann_in & -r_innann_out) | (+r_outann_in & -r_outann_out))

#NEED TO ADD ZIRCONIUM SLEEVE AROUND THE STEEL PIN









support_cell = openmc.Cell(fill=graphite, region=-inner_hex & +min_z & -max_z & +r_support_pin)
support_nbc_cell = openmc.Cell(fill=nbc, region=+inner_hex & -outer_hex & +min_z & -max_z)
support_universe = openmc.Universe(cells=[support_cell, support_nbc_cell, ss_cell, sup_prop_cell])











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
            ring_univs.append(fuel_element_universe)
        elif (ring == 16):
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

# # # Reflector # # #

r_ref = 47.47 # cm
r_reflector = openmc.ZCylinder(r=r_ref)
reflector_cell = openmc.Cell(fill=graphite, region=~dodec_2d & -r_reflector)

# Assembling Fuel into Dodecahedron
assembly_cell = openmc.Cell(fill=assembly_lattice,
                            region=assembly_dodec & +min_z & -max_z)

reactor_universe = openmc.Universe(cells=[assembly_cell, reflector_cell])

geometry = openmc.Geometry(reactor_universe)
geometry.export_to_xml()


mcolors = {
    prop: 'blue',
    fuel: 'green',
    graphite: 'grey',
    nbc: 'black',
    ss: 'yellow'
}

#XY Cross Section
plot1 = openmc.Plot()
plot1.filename = 'Core_Loading_CS_xy'
plot1.origin = (0, 0, reactor_height/2)
plot1.width = (100, 100)
plot1.pixels = (6000, 6000)
plot1.color_by = 'material'
plot1.colors = mcolors
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
#XY Cross Section Cell Color
plot4 = openmc.Plot()
plot4.filename = 'Core_Loading_CS_xy_CellColor'
plot4.origin = (0, 0, reactor_height/2)
plot4.width = (100, 100)
plot4.pixels = (5000, 5000)
plot4.color_by = 'cell'

#plots = openmc.Plots([plot1, plot2, plot3, plot4])
plots = openmc.Plots([plot1, plot4])
plots.export_to_xml()

openmc.plot_geometry()
