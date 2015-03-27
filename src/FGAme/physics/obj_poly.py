# -*- coding: utf8 -*-

from FGAme.physics.obj_all import RigidBody
from FGAme.mathutils import aabb_bbox
from FGAme.mathutils import Vector, VectorM, RotMatrix, dot, cross
from FGAme.mathutils import area, center_of_mass, ROG_sqr
from FGAme.mathutils import sin, cos, pi

__all__ = ['Poly', 'RegularPoly', 'Rectangle']


class Poly(RigidBody):

    '''Define um polígono arbitrário de N lados.'''

    __slots__ = ['_vertices', 'num_sides', '_normals_idxs', 'num_normals']

    def __init__(self,
                 vertices,
                 pos=None, vel=(0, 0), theta=0.0, omega=0.0,
                 mass=None, density=None, inertia=None):

        vertices = [VectorM(*pt) for pt in vertices]
        pos_cm = center_of_mass(vertices)
        vertices = [v - pos_cm for v in vertices]
        self._vertices = vertices

        # Cache de vértices
        self._cache_theta = None
        self._cache_rvertices_last = None
        self._cache_rbbox_last = None
        self.cbb_radius = max(v.norm() for v in vertices)
        super(Poly, self).__init__(pos_cm, vel, theta, omega,
                                   mass=mass, density=density, inertia=inertia)

        self.num_sides = len(vertices)
        self._normals_idxs = self.get_li_indexes()
        self.num_normals = len(self._normals_idxs or self.vertices)

        # Aceleramos um pouco o cálculo para o caso onde todas as normais são
        # LI. entre si. Isto é sinalizado por self._normals_idx = None, que
        # implica que todas as normais do polígono devem ser recalculadas a
        # cada frame
        if self.num_normals == self.num_sides:
            self._normals_idxs = None

        # Movemos para a posição especificada caso pos seja fornecido
        if pos is not None:
            self.pos = pos_cm

    def get_li_indexes(self):
        '''Retorna os índices referents às normais linearmente independentes
        entre si.

        Este método é invocado apenas na inicialização do objeto e pode
        involver testes de independencia linear relativamente caros.
        '''

        normals = [self.get_normal(i).normalized()
                   for i in range(self.num_sides)]
        LI = []
        LI_idx = []
        for idx, n in enumerate(normals):
            for n_other in LI:
                # Produto vetorial nulo ==> dependência linear
                if abs(cross(n, n_other)) < 1e-3:
                    break
            else:
                # Executado se o loop "for" não terminar em um break
                # Implica em independência linear
                LI.append(n)
                LI_idx.append(idx)
        return LI_idx

    def get_side(self, i):
        '''Retorna um vetor na direção do i-ésimo lado do polígno. Cada
        segmento é definido pela diferença entre o (i+1)-ésimo ponto e o
        i-ésimo ponto.
        '''

        points = self.vertices
        return points[(i + 1) % self.num_sides] - points[i]

    def get_normal(self, i):
        '''Retorna a normal unitária associada ao i-ésimo segmento. Cada
        segmento é definido pela diferença entre o (i+1)-ésimo ponto e o
        i-ésimo ponto.'''

        points = self.vertices
        x, y = points[(i + 1) % self.num_sides] - points[i]
        return Vector(y, -x).normalized()

    def get_normals(self):
        '''Retorna uma lista com as normais linearmente independentes.'''

        if self._normals_idxs is None:
            N = self.num_sides
            points = self.vertices
            segmentos = (points[(i + 1) % N] - points[i] for i in range(N))
            return [Vector(y, -x).normalized() for (x, y) in segmentos]
        else:
            return [self.get_normal(i) for i in self._normals_idxs]

    def is_internal_point(self, pt):
        '''Retorna True se um ponto for interno ao polígono.'''

        n = self.get_normal
        P = self.vertices
        return all(dot(pt - P[i], n(i)) <= 0 for i in range(self.num_sides))

    ###########################################################################
    #                     Sobrescrita de métodos
    ###########################################################################
    @property
    def vertices(self):
        pos = self.pos
        return [v + pos for v in self._rvertices]

    @property
    def _rvertices(self):
        if self._theta == self._cache_theta:
            return self._cache_rvertices_last
        else:
            R = RotMatrix(self.theta)
            vert = [R * v for v in self._vertices]
            xmin = min(v.x for v in vert)
            xmax = max(v.x for v in vert)
            ymin = min(v.y for v in vert)
            ymax = max(v.y for v in vert)
            bbox = (xmin, xmax, ymin, ymax)

            self._cache_rvertices_last = vert
            self._cache_theta = self._theta
            self._cache_rbbox_last = bbox

            return vert

    @property
    def _rbbox(self):
        if self._theta == self._cache_theta:
            return self._cache_rbbox_last
        else:
            self._rvertices
            return self._cache_rbbox_last

    def scale(self, scale, update_physics=False):
        self._vertices = [scale * v for v in self._vertices]

    def area(self):
        return area(self._vertices)

    def ROG_sqr(self):
        return ROG_sqr(self._vertices)

    @property
    def xmin(self):
        return self._pos.x + self._rbbox[0]

    @property
    def xmax(self):
        return self._pos.x + self._rbbox[1]

    @property
    def ymin(self):
        return self._pos.y + self._rbbox[2]

    @property
    def ymax(self):
        return self._pos.y + + self._rbbox[3]

###############################################################################
#                         Especialização de polígonos
###############################################################################


class RegularPoly(Poly):

    __slots__ = ['length']

    def __init__(self, N, length,
                 pos=(0, 0), vel=(0, 0), theta=0.0, omega=0.0,
                 mass=None, density=None, inertia=None):
        '''Cria um polígono regoular com N lados de tamanho "length".'''

        self.length = length
        vertices = self._vertices(N, length, pos)
        del N, length, pos

        Poly.__init__(**locals())

    def _vertices(self, N, length, pos):
        self.length = length
        alpha = pi / N
        theta = 2 * alpha
        b = length / (2 * sin(alpha))
        P0 = Vector(b, 0)
        pos = Vector(*pos)
        return [(P0.rotated(n * theta)) + pos for n in range(N)]


class Rectangle(Poly):

    __slots__ = []

    def __init__(self, xmin=None, xmax=None, ymin=None, ymax=None,
                 pos=None, vel=(0, 0), theta=0.0, omega=0.0,
                 mass=None, density=None, inertia=None,
                 bbox=None, rect=None, shape=None):
        '''Cria um retângulo especificando ou a caixa de contorno ou a posição
        do centro de massa e a forma.

        Pode ser inicializado como uma AABB, mas gera um polígono como
        resultado.

        >>> r = Rectangle(shape=(200, 100))
        >>> r.rotate(pi/4)
        >>> r.bbox                                         # doctest: +ELLIPSIS
        (-106.066..., 106.066..., -106.066..., 106.066...)

        '''

        bbox = aabb_bbox(bbox=bbox, rect=rect, shape=shape, pos=pos,
                         xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)
        xmin, xmax, ymin, ymax = bbox

        super(Rectangle, self).__init__(
            [(xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)],
            None, vel, theta, omega,
            mass=mass, density=density, inertia=inertia
        )


@classmethod
def triangle(cls, sides, pos=(0, 0), **kwds):
    '''Cria um triângulo especificando o tamanho dos lados'''
    pass


@classmethod
def blob(cls, N, scale, pos=(0, 0), **kwds):
    '''Cria um polígono convexo aleatório especificando o número de lados e
    um fator de escala.'''
    pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()
