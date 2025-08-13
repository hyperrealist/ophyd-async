import asyncio
from math import radians, sin, cos, sqrt

import pytest
from bluesky import RunEngine
from bluesky.utils import MsgGenerator
from bluesky import plan_stubs as bps

from ophyd_async.core import Device, soft_signal_rw, derived_signal_rw, enhanced_gather


@pytest.fixture
async def multi_signal_device():
    class MultiSignalDevice(Device):
        def __init__(self, prefix: str = "", name: str = ""):
            self.x = soft_signal_rw(float, 0.0, "x")
            self.y = soft_signal_rw(float, 0.0, "y")
            self.theta = soft_signal_rw(float, 30.0, "theta")
            self.r = derived_signal_rw(self._get_r,
                                       self._set_r,
                                       x=self.x,
                                       y=self.y,
                                       name="r")
            super().__init__(name)

        def _get_r(self, x: float, y: float) -> float:
            return sqrt(x * x + y * y)

        async def _set_r(self, r: float):
            theta = await self.theta.get_value()
            await enhanced_gather(
                    self.x.set(r * cos(radians(theta))),
                    self.y.set(r * sin(radians(theta))),
            )

    device = MultiSignalDevice("msd")
    await device.connect(mock=True)

    async def take_too_long(*args, **kwargs):
        await asyncio.sleep(20)

    device.y._connector.backend.put = take_too_long
    return device


@pytest.mark.timeout(15)
def test_timeout_error_details_longer_than_standard_timeout(multi_signal_device):
    def set_r() -> MsgGenerator:
        yield from bps.abs_set(multi_signal_device.r, 10, wait=True)

    RE = RunEngine()
    RE(set_r())
