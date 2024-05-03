"""A collection of all commands that Adele can use to interact with the game. 	"""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up


# List of key mappings
class Key:
    # Movement
    JUMP = 'ctrl'
    TELEPORT = 'alt'

    # Skills
    BIGBANG = 'a'
    ANGEL_RAY = 's'
    DIVINE_PUNISHMENT = 'd'
    PEACEMAKER = '1'
    GENESIS = '2'
    HEAVENS_DOOR = '3'
    FOUNTAIN_OF_VENGEANCE = 'end'
    ERDA_SHOWER = 'delete'

    # Buffs
    INFINITY = 'f1'
    UNRELIABLE_MEMORY = 'f2'
    ANGEL_OF_BALANCE = 'f3'
    BENEDICTION = 'f4'
    EPIC_ADVENTURE = 'shift'
    MAPLE_WORLD_GODDESS_BLESSING = 'c'


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Auto Maple.
    """

    # num_presses = 2
    # if direction == 'up' or direction == 'down':
    #     num_presses = 1
    num_presses = 1
    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_y = target[1] - config.player_pos[1]
    if abs(d_y) > settings.move_tolerance * 1.5:
        if direction == 'down':
            press(Key.JUMP, 3)
        elif direction == 'up':
            press(Key.JUMP, 1)
    press(Key.TELEPORT, num_presses)


class Adjust(Command):
    """Fine-tunes player position using small movements."""

    def __init__(self, x, y, max_steps=5):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps
        toggle = True
        error = utils.distance(config.player_pos, self.target)
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                threshold = settings.adjust_tolerance / math.sqrt(2)
                if abs(d_x) > threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):
                    if d_y < 0:
                        Teleport('up').main()
                    else:
                        key_down('down')
                        time.sleep(0.05)
                        press(Key.JUMP, 3, down_time=0.1)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle


class Teleport(Command):
    """
    Teleports in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    def __init__(self, direction, jump='False'):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)
        self.jump = settings.validate_boolean(jump)

    def main(self):
        # num_presses = 3
        num_presses = 1
        time.sleep(0.05)
        if self.direction in ['up', 'down']:
            num_presses = 2
        if self.direction != 'up':
            key_down(self.direction)
            time.sleep(0.05)
        if self.jump:
            if self.direction == 'down':
                press(Key.JUMP, 3, down_time=0.1)
            else:
                press(Key.JUMP, 1)
        if self.direction == 'up':
            key_down(self.direction)
            time.sleep(0.05)
        press(Key.TELEPORT, num_presses)
        key_up(self.direction)
        if settings.record_layout:
            config.layout.add(*config.player_pos)


class BigBang(Command):
    def __init__(self, repetitions=1):
        super().__init__(locals())
        self.repetitions = int(repetitions)

    def main(self):
        for i in range(self.repetitions):
            press(Key.BIGBANG, 1, up_time=0.05)
            time.sleep(0.3)


class PeaceMaker(Command):
    def main(self):
        press(Key.PEACEMAKER, 2, up_time=0.05)
        time.sleep(0.2)
        press(Key.PEACEMAKER, 2, up_time=0.05)


class Genesis(Command):
    def main(self):
        press(Key.GENESIS, 1, up_time=0.05)


class HeavensDoor(Command):
    def main(self):
        press(Key.HEAVENS_DOOR, 1, up_time=0.05)


class FountainOfVengeance(Command):
    def main(self):
        press(Key.FOUNTAIN_OF_VENGEANCE, 3, up_time=0.05)
        time.sleep(0.5)


class ErdaShower(Command):
    def main(self):
        press(Key.ERDA_SHOWER, 3, up_time=0.05)
        time.sleep(0.5)


class Buff(Command):
    """Uses each of Adele's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.cd90_buff_time = 0
        self.cd120_buff_time = 0
        self.cd180_buff_time = 0
        self.cd200_buff_time = 0
        self.cd240_buff_time = 0
        self.cd900_buff_time = 0
        self.infinity_toggle = True

    def main(self):
        now = time.time()
        if self.cd90_buff_time == 0 or now - self.cd90_buff_time > 90:
            press(Key.MAPLE_WORLD_GODDESS_BLESSING, 2)
            time.sleep(0.3)
            if self.infinity_toggle:
                press(Key.INFINITY, 2)
                time.sleep(0.3)
                self.infinity_toggle = False
            else:
                press(Key.UNRELIABLE_MEMORY, 2)
                time.sleep(0.3)
                self.infinity_toggle = True
            self.cd90_buff_time = now
        if self.cd120_buff_time == 0 or now - self.cd120_buff_time > 120:
            press(Key.ANGEL_OF_BALANCE, 2)
            time.sleep(0.3)
            press(Key.BENEDICTION, 2)
            time.sleep(0.3)
            press(Key.EPIC_ADVENTURE, 2)
            time.sleep(0.3)
            self.cd120_buff_time = now
        if self.cd180_buff_time == 0 or now - self.cd180_buff_time > 180:
            self.cd180_buff_time = now
        if self.cd200_buff_time == 0 or now - self.cd200_buff_time > 200:
            self.cd200_buff_time = now
        if self.cd240_buff_time == 0 or now - self.cd240_buff_time > 240:
            self.cd240_buff_time = now
        if self.cd900_buff_time == 0 or now - self.cd900_buff_time > 900:
            self.cd900_buff_time = now


# class Resonance(Command):
#     """
#     Resonance in a given direction, jumping if specified. Adds the player's position
#     to the current Layout if necessary.
#     """
#
#     def __init__(self, direction, jump='False'):
#         super().__init__(locals())
#         self.direction = settings.validate_arrows(direction)
#         self.jump = settings.validate_boolean(jump)
#
#     def main(self):
#         num_presses = 3
#         time.sleep(0.05)
#         if self.direction in ['up', 'down']:
#             num_presses = 2
#         if self.direction != 'up':
#             key_down(self.direction)
#             time.sleep(0.05)
#         if self.jump:
#             if self.direction == 'down':
#                 press(Key.JUMP, 3, down_time=0.1)
#             else:
#                 press(Key.JUMP, 1)
#         if self.direction == 'up':
#             key_down(self.direction)
#             time.sleep(0.05)
#         press(Key.RESONANCE, num_presses)
#         key_up(self.direction)
#         if settings.record_layout:
#             config.layout.add(*config.player_pos)
#
#
# class Impale(Command):
#     """
#     Impale in a given direction, jumping if specified. Adds the player's position
#     to the current Layout if necessary.
#     """
#
#     def __init__(self, direction, jump='False'):
#         super().__init__(locals())
#         self.direction = settings.validate_arrows(direction)
#         self.jump = settings.validate_boolean(jump)
#
#     def main(self):
#         num_presses = 3
#         time.sleep(0.05)
#         if self.direction in ['up', 'down']:
#             num_presses = 2
#         if self.direction != 'up':
#             key_down(self.direction)
#             time.sleep(0.05)
#         if self.jump:
#             if self.direction == 'down':
#                 press(Key.JUMP, 3, down_time=0.1)
#             else:
#                 press(Key.JUMP, 1)
#         if self.direction == 'up':
#             key_down(self.direction)
#             time.sleep(0.05)
#         press(Key.IMPALE, num_presses)
#         key_up(self.direction)
#         if settings.record_layout:
#             config.layout.add(*config.player_pos)
#
#
# class Cleave(Command):
#     """Attacks using 'Cleave' in a given direction."""
#
#     def __init__(self, direction, attacks=2, repetitions=1):
#         super().__init__(locals())
#         self.direction = settings.validate_horizontal_arrows(direction)
#         self.attacks = int(attacks)
#         self.repetitions = int(repetitions)
#
#     def main(self):
#         time.sleep(0.05)
#         key_down(self.direction)
#         time.sleep(0.05)
#         if config.stage_fright and utils.bernoulli(0.7):
#             time.sleep(utils.rand_float(0.1, 0.3))
#         for _ in range(self.repetitions):
#             press(Key.CLEAVE, self.attacks, up_time=0.05)
#         key_up(self.direction)
#         if self.attacks > 2:
#             time.sleep(0.3)
#         else:
#             time.sleep(0.2)
#
#
# class HuntingDecree(Command):
#     """Uses 'Hunting Decree' once."""
#
#     def main(self):
#         press(Key.HUNTING_DECREE, 1, up_time=0.05)
#
#
# class NobleSummons(Command):
#     """Uses 'Noble summons' once."""
#
#     def main(self):
#         press(Key.NOBLE_SUMMONS, 1, up_time=0.05)
#
#
# class AetherBloom(Command):
#     """Uses 'Aether Bloom' once."""
#
#     def main(self):
#         press(Key.AETHER_BLOOM, 1, up_time=0.05)
#
#
# class MagicDispatch(Command):
#     """Uses 'Magic Dispatch' once."""
#
#     def main(self):
#         press(Key.MAGIC_DISPATCH, 1, up_time=0.05)
#
#
# class LucidSoul(Command):
#     """
#     Places 'Lucid Soul Summon' in a given direction, or towards the center of the map if
#     no direction is specified.
#     """
#
#     def __init__(self, direction=None):
#         super().__init__(locals())
#         if direction is None:
#             self.direction = direction
#         else:
#             self.direction = settings.validate_horizontal_arrows(direction)
#
#     def main(self):
#         if self.direction:
#             press(self.direction, 1, down_time=0.1, up_time=0.05)
#         else:
#             if config.player_pos[0] > 0.5:
#                 press('left', 1, down_time=0.1, up_time=0.05)
#             else:
#                 press('right', 1, down_time=0.1, up_time=0.05)
#         press(Key.LUCID_SOUL, 3)
#
#
# class ReignOfDestruction(Command):
#     """
#     Uses 'Reign of destruction' in a given direction, or towards the center of the map if
#     no direction is specified.
#     """
#
#     def __init__(self, direction=None):
#         super().__init__(locals())
#         if direction is None:
#             self.direction = direction
#         else:
#             self.direction = settings.validate_horizontal_arrows(direction)
#
#     def main(self):
#         if self.direction:
#             press(self.direction, 1, down_time=0.1, up_time=0.05)
#         else:
#             if config.player_pos[0] > 0.5:
#                 press('left', 1, down_time=0.1, up_time=0.05)
#             else:
#                 press('right', 1, down_time=0.1, up_time=0.05)
#         press(Key.REIGN_OF_DESTRUCTION, 3)
#
#
# class Shardbreaker(Command):
#     """
#     Uses 'Shardbreaker' in a given direction, or towards the center of the map if
#     no direction is specified.
#     """
#
#     def __init__(self, direction=None):
#         super().__init__(locals())
#         if direction is None:
#             self.direction = direction
#         else:
#             self.direction = settings.validate_horizontal_arrows(direction)
#
#     def main(self):
#         if self.direction:
#             press(self.direction, 1, down_time=0.1, up_time=0.05)
#         else:
#             if config.player_pos[0] > 0.5:
#                 press('left', 1, down_time=0.1, up_time=0.05)
#             else:
#                 press('right', 1, down_time=0.1, up_time=0.05)
#         press(Key.SHARDBREAKER, 3)
#
#
# class Ruin(Command):
#     """Uses 'Ruin' once."""
#
#     def main(self):
#         press(Key.RUIN, 3)
#
#
# class Arachnid(Command):
#     """Uses 'True Arachnid Reflection' once."""
#
#     def main(self):
#         press(Key.ARACHNID, 3)
#
#
# class HighRise(Command):
#     """Uses 'High Rise' once to stay in the air."""
#
#     def __init__(self, jump='False'):
#         super().__init__(locals())
#         self.jump = settings.validate_boolean(jump)
#
#     def main(self):
#         if self.jump:
#             press(Key.JUMP, 1, down_time=0.1, up_time=0.15)
#         press(Key.HIGH_RISE, 2, up_time=0.05)
#
#
# class Plummet(Command):
#     """Uses 'Plummet' once to attack downwards."""
#
#     def __init__(self, jump='False'):
#         super().__init__(locals())
#         self.jump = settings.validate_boolean(jump)
#
#     def main(self):
#         if self.jump:
#             press(Key.JUMP, 1, down_time=0.1, up_time=0.15)
#         press(Key.PLUMMET, 2, up_time=0.05)
#
#
# class FeatherFloat(Command):
#     """Jumps backwards using 'Feather Float' once."""
#
#     def __init__(self, jump='False'):
#         super().__init__(locals())
#         self.jump = settings.validate_boolean(jump)
#
#     def main(self):
#         if self.jump:
#             press(Key.JUMP, 1, down_time=0.1, up_time=0.15)
#         press(Key.FEATHER_FLOAT, 2, up_time=0.05)
#
#
# class Storm(Command):
#     """Uses 'Storm' once."""
#
#     def main(self):
#         press(Key.STORM, 3)
#
#
# class BladeTorrent(Command):
#     """Uses 'Blade Torrent' once."""
#
#     def main(self):
#         press(Key.BLADE_TORRENT, 2, down_time=0.1)
#
#
# class InfinityBlade(Command):
#     """Uses 'Infinity Blade' once."""
#
#     def main(self):
#         press(Key.INFINITY_BLADE, 2, down_time=0.1)
#
#
# class ErdaShower(Command):
#     """Uses 'Erda Shower' once."""
#
#     def main(self):
#         press(Key.ERDA_SHOWER, 2, down_time=0.1)
#
#
# class TrueNobility(Command):
#     """Places a'True nobility' field on the ground once."""
#
#     def main(self):
#         press(Key.TRUE_NOBILITY, 2)
#
#
# class GraveProclamation(Command):
#     """Uses 'Grave proclamation' to mark an enemy once."""
#
#     def main(self):
#         press(Key.GRAVE_PROCLAMATION, 2)
