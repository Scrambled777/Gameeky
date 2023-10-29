from .base import Actuator as BaseActuator

from ....common.definitions import Action


class Actuator(BaseActuator):
    name = "destroys"
    interactable = False
    activatable = True

    def tick(self) -> None:
        if self._entity.durability <= 0 or self.activated is True:
            self._entity.stop()
            self._entity.perform(Action.DESTROY)

        super().tick()
