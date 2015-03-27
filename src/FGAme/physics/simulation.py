# -*- coding: utf8 -*-

from FGAme.mathutils import Vector, shadow_y
from FGAme.physics import get_collision, get_collision_aabb, CollisionError
from FGAme.physics import flags
from FGAme.core import EventDispatcher, signal, init
from FGAme.core import env
from FGAme.physics.flags import ACCEL_STATIC

###############################################################################
#                                Simulação
# ----------------------------------------------------------------------------
# Coordena todos os objetos com uma física definida e resolve a interação
# entre eles
###############################################################################


class Simulation(EventDispatcher):

    '''Implementa a simulação de física.

    Os métodos principais são: add(obj) e remove(obj) para adicionar e remover
    objetos e update(dt) para atualizar o estado da simulação. Verifique a
    documentação do método update() para uma descrição detalhada sobre como
    a física é resolvida em cada etapa de simulação.
    '''

    def __init__(self, gravity=None, damping=0, adamping=0,
                 rest_coeff=1, sfriction=0, dfriction=0, stop_velocity=1e-6):

        super(Simulation, self).__init__()
        self._dt = 0.0
        self._objects = []
        self._broad_collisions = []
        self._fine_collisions = []

        # Inicia a gravidade e as constantes de força dissipativa
        self.gravity = gravity or (0, 0)
        self.damping = damping
        self.adamping = adamping

        # Colisão
        self.rest_coeff = float(rest_coeff)
        self.sfriction = float(sfriction)
        self.dfriction = float(dfriction)
        self.stop_velocity = float(stop_velocity)
        self.time = 0

    ###########################################################################
    #                           Serviços Python
    ###########################################################################
    def __iter__(self):
        return iter(self._objects)

    def __contains__(self, obj):
        return obj in self._objects

    frame_enter = signal('frame-enter')
    collision = signal('collision', num_args=1)

    ###########################################################################
    #                             Propriedades
    ###########################################################################

    @property
    def gravity(self):
        return self._gravity

    @gravity.setter
    def gravity(self, value):
        try:
            gravity = self._gravity = Vector(*value)
        except TypeError:
            gravity = self._gravity = Vector(0, -value)

        for obj in self:
            if not obj.owns_gravity:
                obj._gravity = gravity

    @property
    def damping(self):
        return self._damping

    @damping.setter
    def damping(self, value):
        value = self._damping = float(value)

        for obj in self._objects:
            if not obj.owns_damping:
                obj._damping = value

    @property
    def adamping(self):
        return self._adamping

    @adamping.setter
    def adamping(self, value):
        value = self._adamping = float(value)

        for obj in self._objects:
            if not obj.owns_adamping:
                obj._adamping = value

    ###########################################################################
    #                   Gerenciamento de objetos e colisões
    ###########################################################################
    def add(self, obj):
        '''Adiciona um novo objeto ao mundo.

        Exemplos
        --------

        >>> from FGAme import *
        >>> obj = AABB(bbox=(-10, 10, -10, 10))
        >>> world = World()
        >>> world.add(obj, layer=1)
        '''

        if obj not in self._objects:
            self._objects.append(obj)
            if not obj.owns_gravity:
                obj._gravity = self.gravity
            if not obj.owns_damping:
                obj._damping = self.damping
            if not obj.owns_adamping:
                obj._adamping = self.adamping

    def remove(self, obj):
        '''Descarta um objeto da simulação'''

        try:
            del self._objects[self._objects.index(obj)]
        except IndexError:
            pass

    ###########################################################################
    #                     Simulação de Física
    ###########################################################################
    def update(self, dt):
        '''Rotina principal da simulação de física.'''

        self.trigger_frame_enter()
        self._dt = float(dt)

        self.broad_phase()
        self.fine_phase()
        self.update_accelerations()
        self.resolve_accelerations()
        self.resolve_collisions()

        self.time += self._dt

    def broad_phase(self):
        '''Retorna uma lista com todas as colisões atuais.

        Uma colisão é caracterizada por um objeto da classe Collision() ou
        subclasse.'''

        objects = self._objects
        col_idx = 0
        objects.sort(key=lambda obj: obj.pos.x - obj.cbb_radius)
        self._broad_collisions[:] = []

        # Os objetos estão ordenados. Este loop detecta as colisões da CBB e
        # salva o resultado na lista broad collisions
        for i, A in enumerate(objects):
            A_radius = A.cbb_radius
            A_right = A.pos.x + A_radius
            A_dynamic = A.is_dynamic()

            for j in range(i + 1, len(objects)):
                B = objects[j]
                B_radius = B.cbb_radius

                # Procura na lista enquanto xmin de B for menor que xmax de A
                B_left = B.pos.x - B_radius
                if B_left > A_right:
                    break

                # Não detecta colisão entre dois objetos estáticos/cinemáticos
                if not A_dynamic and not B.is_dynamic():
                    continue

                # Testa a colisão entre os círculos de contorno
                if (A.pos - B.pos).norm() > A_radius + B_radius:
                    continue

                # Adiciona à lista de colisões grosseiras
                col_idx += 1
                self._broad_collisions.append((A, B))

    def fine_phase(self):
        # Detecta colisões e atualiza as listas internas de colisões de
        # cada objeto
        self._fine_collisions[:] = []

        for A, B in self._broad_collisions:
            col = self.get_fine_collision(A, B)

            if col is not None:
                col.world = self
                A.trigger('collision', col)
                B.trigger('collision', col)
                if col.is_active:
                    self._fine_collisions.append(col)

    def update_accelerations(self):
        return

        t = self.time
        ACCEL_STATIC = flags.ACCEL_STATIC
        ALPHA_STATIC = 0  # flags.ALPHA_STATIC

        # Acumula as forças e acelerações
        # FIXME: consertar mecanismo de aceleração externa
        for obj in self._objects:
            if obj._invmass:
                obj.init_accel()
                if obj.force is not None:
                    obj._accel += obj.force(t) * obj._invmass

            elif obj.flags & ACCEL_STATIC:
                obj.init_accel()
                obj.apply_accel(obj._accel, dt)

            if obj._invinertia:
                obj.init_alpha()
                #tau += obj.external_torque(t) or 0

            elif obj.flags & ALPHA_STATIC:
                obj.init_alpha()
                obj.apply_alpha(self._alpha, dt)

    def resolve_accelerations(self):
        '''Resolve a dinâmica de forças durante o intervalo dt'''

        dt = self._dt
        for obj in self._objects:
            if obj._invmass:
                obj.apply_accel(None, dt)
            elif obj._vel.x or obj._vel.y:
                obj.move(obj._vel * dt)

            if obj._invinertia:
                obj.apply_alpha(None, dt)
            elif obj._omega:
                obj.rotate(obj._omega * dt)

    def resolve_collisions(self):
        for col in self._fine_collisions:
            col.resolve()

    def get_fine_collision(self, A, B):
        '''Retorna a colisão entre os objetos A e B depois que a colisão AABB
        foi detectada'''

        try:
            return get_collision(A, B)
        except CollisionError:
            pass

        # Colisão não definida. Primeiro tenta a colisão simétrica e registra
        # o resultado caso bem sucedido. Caso a colisão simétrica também não
        # seja implementada, define a colisão como uma aabb
        try:
            col = get_collision(B, A)
            if col is None:
                return
            col.normal *= -1
        except CollisionError:
            get_collision[type(A), type(B)] = get_collision_aabb
            get_collision[type(B), type(A)] = get_collision_aabb
            return get_collision_aabb(A, B)
        else:
            def inverse(A, B):
                '''Automatically created collision for A, B from the supported
                collision B, A'''
                col = direct(B, A)
                if col is not None:
                    return col.swapped()

            direct = get_collision[type(B), type(A)]
            get_collision[type(A), type(B)] = inverse
            return col

    # Cálculo de parâmetros físicos ###########################################
    def kinetic_energy(self):
        '''Retorna a soma da energia cinética de todos os objetos do mundo'''

        return sum(obj.kinetic() for obj in self.objects)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
