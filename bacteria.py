import random
import os
import datetime
import math

import matplotlib.pyplot as plt
import imageio


MAKE_GIF = False  # Warning. Very inefficient
FRAME_DURATION = 0.3

STEPS = 100

TIME = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
os.makedirs(f'./runs/{TIME}')
os.makedirs(f'./runs/{TIME}/images')
XLIM = [-5, 5]
YLIM = [-5, 5]
plt.xlim(XLIM)
plt.ylim(YLIM)
plt.gca().axes.set_aspect(1)

DROP_FOOD_EACH_N_STEPS = 5
FOOD_MIN_ENERGY = 10
FOOD_MAX_ENERGY = 100

ADAMS_N = 5
MAX_START_SPEED = 5
BACTERIA_MAX_START_ENERGY = 100
MUTATION_CHANCE = 1
MUTATION_VARIANCE = 0.1

SAVE_IMAGE_EACH_N_STEPS = 1
DEATH_MARKERS_PERSIST_FOR_N_STEPS = 3
INIT_EXPLR_RATE = 1
EXPLR_RATE_DECREASE = 0.9  # Multiply
MIN_EXPLR = 0.001


def randangle():
    return 2 * math.pi * random.random() * random.choice((-1, 1))

def drop():
    return random.uniform(XLIM[0], XLIM[1]), random.uniform(YLIM[0], YLIM[1])

food_sources = []
class Food:
    def __init__(self):
        self.x, self.y = drop()
        self.energy = random.randint(FOOD_MIN_ENERGY, FOOD_MAX_ENERGY)
        self.radius = self.energy / 20
        self.eating_b = []
        food_sources.append(self)


bacteria = []
all_bacteria_ever_lived = []
class Bacterium:
    def __init__(self, x=None, y=None, speed=None, max_energy=None, birth_step=1, parent=None):
        if not x and not y:
            self.x, self.y = drop()
        else:
            self.x, self.y = x, y
        if speed is None and max_energy is None:
            self.speed = random.uniform(1, MAX_START_SPEED)
            self.max_energy = random.uniform(1, BACTERIA_MAX_START_ENERGY)
        else:
            self.speed = speed
            self.max_energy = max_energy
        self.birth_step = birth_step
        self.parent = parent
        self.children = []
        self.death_step = None
        self.energy = self.max_energy / 2
        self.eating = False
        self.food = None
        bacteria.append(self)
        all_bacteria_ever_lived.append(self)

    def color(self):
        # RGB. Red for speed, green for max energy
        return min(self.speed / MAX_START_SPEED, 1), min(self.max_energy / BACTERIA_MAX_START_ENERGY, 1), 1

    def closest_food(self):
        """Find closest food and return its coords"""
        # Check if inside a food source:
        for f in food_sources:
            if ((f.x - self.x)**2 + (f.y - self.y)**2)**0.5 <= f.radius:
                return f

        # Check for centers and radiuses:
        closest_dist = math.inf
        closest = None
        for f in food_sources:
            angle = math.atan2(self.y - f.y, self.x - f.x)
            x = f.x + (f.radius * math.cos(angle))
            y = f.y + (f.radius * math.sin(angle))
            dist = ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
            if dist < closest_dist:
                closest_dist = dist
                closest = f
        return closest

    @staticmethod
    def mutation_calc(attr):
        """Does the attr mutate? By how much?"""
        if random.random() <= MUTATION_CHANCE:
            amplitude = attr * MUTATION_VARIANCE
            return random.uniform(attr - amplitude, attr + amplitude)
        else:
            return attr

    def reproduce(self, step):
        """Splitting in 2, both having energy = max_energy/2. The parent needs to have max energy to reproduce"""
        speed = self.mutation_calc(self.speed)
        max_energy = self.mutation_calc(self.max_energy)
        # Spawning close to the parent:
        new_b_x = self.x + random.uniform(-0.5, 0.5)
        new_b_y = self.y + random.uniform(-0.5, 0.5)
        child = Bacterium(new_b_x, new_b_y, speed, max_energy, birth_step=step, parent=self)
        self.children.append(child)

for _ in range(ADAMS_N):
    Bacterium()


Food()
step = 1
reproduced = 0
died = 0
death_list = []
death_markers = []
death_markers_to_be_removed = []
graph_points = [[], []]
while True:
    # Drop food:
    if step % DROP_FOOD_EACH_N_STEPS == 0:
        Food()

    # Draw:
    if step % SAVE_IMAGE_EACH_N_STEPS == 0:
        for f in food_sources:
            circle = plt.Circle((f.x, f.y), f.radius, color='y', alpha=f.energy / (f.radius * 20))
            plt.gca().add_patch(circle)
        for b in bacteria:
            plt.scatter(b.x, b.y, color=b.color())
        for m in death_markers:
            plt.scatter(m[0], m[1], color='black', marker='x', zorder=1)

        plt.title(f'Step: {step}; Bacteria remaining: {len(bacteria)}')
        plt.savefig(f'./runs/{TIME}/images/{step}')
        plt.clf()
        plt.xlim(XLIM)
        plt.ylim(YLIM)
        plt.gca().axes.set_aspect(1)

    # Spend energy no matter what:
    for b in bacteria:
        b.energy -= 0.1
        if b.energy <= 0:
            death_list.append(b)

    # Movement and eating:
    for b in bacteria:
        if b not in death_list:
            if not b.eating:
                f = b.closest_food()
                if f:
                    dist = ((f.x - b.x)**2 + (f.y - b.y)**2)**0.5
                    if dist > f.radius:  # Too far => move closer
                        # Calculating new coordinates
                        A = f.x - b.x
                        B = f.y - b.y
                        C = (A**2 + B**2)**0.5
                        dist_to_move = min(b.speed, C - f.radius)  # No need to overshoot
                        x = A/C * dist_to_move
                        y = B/A * x

                        # If you can't reach food, die now:
                        energy_to_be_removed = dist_to_move * b.speed
                        if b.energy - energy_to_be_removed <= 0:  # Out of energy => death sentence:
                            death_list.append(b)
                        else:
                            b.energy -= energy_to_be_removed
                            b.x += x
                            b.y += y

                    else:  # No need to move => eat
                        b.eating = True
                        b.food = f
                        f.eating_b.append(b)
            else:  # Eating
                f = b.food
                f.energy -= 1
                b.energy += 1
                if f.energy <= 0:
                    for b_ in f.eating_b:
                        b_.eating = False
                        b_.food = None
                    food_sources.remove(f)
                if b.energy >= b.max_energy:
                    print(f'Reproduction! Step: {step}')
                    b.reproduce(step)
                    reproduced += 1

    # Death:
    for b in death_list:
        print(f'Death! Step: {step}')
        try:
            b.food.eating_b.remove(b)
        except AttributeError:
            pass
        b.death_step = step
        bacteria.remove(b)
        death_markers.append((b.x, b.y, step + DEATH_MARKERS_PERSIST_FOR_N_STEPS))
        died += 1
    death_list = []

    for m in death_markers:
        if m[2] == step:
            death_markers_to_be_removed.append(m)
    for m in death_markers_to_be_removed:
        death_markers.remove(m)
    death_markers_to_be_removed = []

    # Graph:
    graph_points[0].append(step)
    graph_points[1].append(len(bacteria))

    # Finishing the run:
    if step == STEPS:
        print()
        print('Survivors (speed, max energy):')
        b_speed_sum = 0
        b_max_energy_sum = 0
        b_n = 0
        for b in bacteria:
            b_speed_sum += b.speed
            b_max_energy_sum += b.max_energy
            b_n += 1
            print(round(b.speed, 2), round(b.max_energy, 2))
        print(f'Survivors mean speed: {round(b_speed_sum/b_n, 2)};', end=' ')
        print(f'Survivors mean max energy: {round(b_max_energy_sum/b_n, 2)}')
        print(f'Initial number: {ADAMS_N}; Survived: {len(bacteria)}; Reproduced: {reproduced}; Died: {died}')
        break
    elif not bacteria:
        print()
        print("Everyone died!")
        print(f'Initial number: {ADAMS_N}; Survived: {len(bacteria)}; Reproduced: {reproduced}; Died: {died}')
        break
    step += 1

# Population graph:
plt.clf()
plt.fill_between(graph_points[0], graph_points[1])
plt.title('Population graph')
plt.savefig(f'./runs/{TIME}/population_graph.png')

# Evo forest:
plt.clf()
plt.gca().get_yaxis().set_visible(False)
for b in all_bacteria_ever_lived:
    if not b.death_step:  # No death_step because alive at the end of the run
        b.death_step = step
y = 0
def tree(b):
    global y
    b.children.sort(key=lambda c: int(c.birth_step), reverse=True)
    b.evo_forest_y = y
    y += 1
    for c in b.children:
        tree(c)
    plt.plot((b.birth_step, b.birth_step, b.death_step), (b.parent.evo_forest_y, b.evo_forest_y, b.evo_forest_y), color=b.color())
adams = [b for b in all_bacteria_ever_lived if not b.parent]
for adam in adams:
    adam.evo_forest_y = y
    plt.plot((adam.birth_step, adam.death_step), (adam.evo_forest_y, adam.evo_forest_y), color=adam.color())
    y += 1
    adam.children.sort(key=lambda c: int(c.birth_step), reverse=True)
    for c in adam.children:
        tree(c)
plt.title('Evo forest')
plt.savefig(f'./runs/{TIME}/evo_forest.png')

# GIF:
if MAKE_GIF:
    filenames = sorted(os.listdir(f'./runs/{TIME}/images'), key=lambda x: int(x[:-4]))
    images = []
    for filename in filenames:
        images.append(imageio.imread(f'./runs/{TIME}/images/{filename}'))
    imageio.mimsave(f'./runs/{TIME}/demo.gif', images, duration=FRAME_DURATION)
    print('GIF created')