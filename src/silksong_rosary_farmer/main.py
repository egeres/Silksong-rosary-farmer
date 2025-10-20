from datetime import timedelta
import time
from typing import Literal

import mss
import numpy as np
from pynput.keyboard import Controller, Key
from rich import print

from silksong_rosary_farmer.image import (
    color_2_room_is_loading,
    img_2_color_centroid,
    img_2_coloravg,
)
from silksong_rosary_farmer.utils import hex_to_rgb, setup_escape_exit


def farm(
    monitor_inex: int,
    max_time: timedelta | None = None,
) -> None:
    max_time = max_time or timedelta(minutes=999_999_999)

    # Pre
    location_prev = "none"
    last_location = ""
    cooldown_update = time.time()
    cooldown_timer = 1
    behaviour = "tavern_exit"
    keyboard = Controller()
    color_hornet_dress = "#ae3446"
    color_hornet_dress_rgb = hex_to_rgb(color_hornet_dress)
    color_hornet_dress_tolerance = 20
    start_time = time.time()
    time_last_room_change = time.time()
    prev_room_type = "none"
    should_stop = False

    def color_2_room(
        color: tuple[float, float, float, float],
    ) -> Literal["tavern", "exterior", "cave"]:
        """Analyze room type based on RGB color values and the history of past rooms"""
        nonlocal cooldown_update
        nonlocal last_location
        nonlocal location_prev
        r, g, b, w = color

        # If both green and red are greater than blue, we are at the tavern
        if g > b and r > b:
            location_prev = last_location
            last_location = "tavern"
            return "tavern"
        else:
            if last_location == "":
                last_location = "cave"
                return "cave"

        if (
            last_location == "tavern"
            and color_2_room_is_loading(color)
            and time.time() - cooldown_update > cooldown_timer
        ):
            cooldown_update = time.time()
            location_prev = last_location
            last_location = "exterior"
            return "exterior"

        if (
            last_location == "exterior"
            and color_2_room_is_loading(color)
            and time.time() - cooldown_update > cooldown_timer
        ):
            cooldown_update = time.time()
            if location_prev == "cave":
                location_prev = last_location
                last_location = "tavern"
                return "tavern"
            else:
                location_prev = last_location
                last_location = "cave"
                return "cave"

        if (
            last_location == "cave"
            and color_2_room_is_loading(color)
            and time.time() - cooldown_update > cooldown_timer
        ):
            cooldown_update = time.time()
            location_prev = last_location
            last_location = "exterior"
            return "exterior"

        return last_location

    # fmt: off
    def release_all_keys():
        try:
            keyboard.release(Key.right)
            keyboard.release(Key.left)
            keyboard.release(Key.up)
            keyboard.release("c")
            keyboard.release("x")
            keyboard.release("z")
        except Exception:
            pass
    listener = setup_escape_exit(release_keys_func=release_all_keys)
    # fmt: on

    # Loop
    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            if should_stop:
                break
            if time.time() - start_time > max_time.total_seconds():
                print("Max time reached!")
                break

            try:
                # 🍑 Screenshot
                screenshot = sct.grab(monitor)
                w, h = screenshot.width, screenshot.height
                img_bgra = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                    h, w, 4
                )
                img_scaled = img_bgra[::2, ::2, [2, 1, 0]]
                # Set the top-left square of the image to black, this helps to avoid
                # windows notifications like spotify, etc as well as different
                # selections of tools, hearts bla bla bla
                img_scaled[
                    0 : int(img_scaled.shape[0] * 0.21),
                    0 : int(img_scaled.shape[1] * 0.3),
                    :,
                ] = 0
                # from matplotlib import pyplot as plt
                # plt.figure(figsize=(12, 8))
                # plt.imshow(img_scaled)
                # plt.axis("off")
                # plt.title("Right Monitor Screenshot (50% scaled, NEAREST ...)")
                # plt.tight_layout()
                # plt.show()

                # 🍑 Room
                avg_color = img_2_coloravg(img_scaled)
                room_type = color_2_room(avg_color)
                if room_type != prev_room_type:
                    time_last_room_change = time.time()
                    prev_room_type = room_type
                # print(f"Beh {behaviour} Room: {room_type} Room prev: {location_prev}")

                # 🍑 Behaviour control
                if behaviour == "tavern_exit" and room_type == "exterior":
                    behaviour = "exterior_go_cave"
                if behaviour == "exterior_go_cave" and room_type == "cave":
                    print("Fighting enemies")
                    behaviour = "cave_fight"
                if behaviour == "cave_go_exterior" and room_type == "exterior":
                    behaviour = "exterior_go_tavern"
                if behaviour == "exterior_go_tavern" and room_type == "tavern":
                    behaviour = "tavern_go_bench"
                if behaviour == "cave_go_exterior" and room_type == "tavern":
                    behaviour = "tavern_go_bench"
                if behaviour == "tavern_go_bench" and room_type == "exterior":
                    behaviour = "exterior_go_tavern"
                if (
                    behaviour in ["tavern_exit", "exterior_go_cave"]
                    and (time.time() - time_last_room_change) > 60
                ):
                    # Sometimes hornet gets fucking stuck at the rihg end of the cave
                    # and since there are like, some floating objects or something we
                    # can't get her location, this doesn't usually happen, but to
                    # prevent the autofarmer from getting completely blocked we can set
                    # a timer off and if a long time has passed with no acitivty, then
                    # she enables "go back mode"
                    print("I think... hornet is stuck at the right end of the cave?")
                    print("I'll go backkk")
                    behaviour = "cave_go_exterior"
                    last_location = "cave"
                    room_type = "cave"

                # 🍑 Behaviours
                if behaviour == "exterior_go_cave":
                    # We go riiight
                    keyboard.press(Key.right)
                    time.sleep(0.1)
                    keyboard.press("c")
                    time.sleep(0.5)
                    keyboard.release("c")
                    time.sleep(0.3)
                    keyboard.release(Key.right)

                elif behaviour == "exterior_go_tavern":
                    # We go leeeft
                    keyboard.press(Key.left)
                    time.sleep(0.2)
                    keyboard.press("c")
                    time.sleep(0.4)
                    keyboard.release("c")
                    time.sleep(0.3)
                    keyboard.release(Key.left)

                elif behaviour == "cave_fight":
                    # Initial dash to the right until we reach the enemies
                    keyboard.press(Key.right)
                    time.sleep(0.2)
                    keyboard.press("c")
                    time.sleep(1.4)
                    keyboard.release("c")
                    keyboard.release(Key.right)
                    time.sleep(0.1)

                    # She atac
                    for _ in range(15):
                        keyboard.press("x")
                        time.sleep(0.1)
                        keyboard.release("x")

                        keyboard.press(Key.left)
                        time.sleep(0.2)
                        keyboard.press("c")
                        time.sleep(0.2)
                        keyboard.release("c")
                        keyboard.release(Key.left)

                        keyboard.press("x")
                        time.sleep(0.1)
                        keyboard.release("x")

                        keyboard.press(Key.right)
                        time.sleep(0.2)
                        keyboard.press("c")
                        time.sleep(0.2)
                        keyboard.release("c")
                        keyboard.release(Key.right)

                    behaviour = "cave_go_exterior"

                elif behaviour == "cave_go_exterior":
                    keyboard.press(Key.left)
                    time.sleep(0.2)
                    keyboard.press("c")
                    keyboard.press("z")
                    time.sleep(0.5)
                    keyboard.release("c")
                    keyboard.release("z")
                    time.sleep(0.3)
                    keyboard.release(Key.left)

                # 🍑 Get hornet location
                result = img_2_color_centroid(
                    img_scaled,
                    color_hornet_dress_rgb,
                    color_hornet_dress_tolerance,
                )
                if not result:
                    # If at this point we don't have a result, we are probably in the
                    # fire of the middle of the tavern, so we just go right to get away
                    # from it
                    keyboard.press(Key.right)
                    time.sleep(0.3)
                    keyboard.release(Key.right)
                    continue
                x, y = result
                # print(f"Coords: x={x:.4f}, y={y:.4f}")

                # 🍑 Behaviours that depend on the location
                if behaviour == "tavern_exit":
                    if y >= 0.7:  # On the floor
                        # We just go right
                        keyboard.press(Key.right)
                        time.sleep(0.2)
                        keyboard.press("c")
                        time.sleep(0.6)
                        keyboard.release("c")
                        keyboard.release(Key.right)

                    elif y >= 0.45:  # On the bench platform
                        # We go left
                        keyboard.press(Key.left)
                        time.sleep(0.1)
                        keyboard.release(Key.left)
                        keyboard.press(Key.left)
                        time.sleep(0.2)
                        keyboard.press("c")
                        time.sleep(0.5)
                        keyboard.release("c")
                        keyboard.release(Key.left)

                        # We go right after we fall for a little bit
                        time.sleep(0.2)
                        keyboard.press(Key.right)
                        time.sleep(0.2)
                        keyboard.press("c")
                        time.sleep(0.7)
                        keyboard.release("c")
                        keyboard.release(Key.right)

                # 🍑 Beh
                elif behaviour == "tavern_go_bench":
                    if y >= 0.7:  # On the floor
                        # First we position ourselves under the right side of the ledge
                        # of the bench platform at the tavern
                        if x < 0.72:
                            keyboard.press(Key.right)
                            time.sleep(0.1)
                            keyboard.release(Key.right)
                        elif x > 0.75:
                            keyboard.press(Key.left)
                            time.sleep(0.1)
                            keyboard.release(Key.left)
                        # Once we are there, we jump and go right
                        else:
                            keyboard.press("z")
                            time.sleep(0.45)
                            keyboard.release("z")
                            keyboard.press(Key.right)
                            time.sleep(0.4)
                            keyboard.release(Key.right)

                            keyboard.press(Key.right)
                            time.sleep(0.1)
                            keyboard.press("c")
                            time.sleep(0.2)
                            keyboard.release("c")
                            keyboard.release(Key.right)

                    elif y >= 0.45:  # On the bench platform
                        # we go right or left depending on the x coordinate
                        if x < 0.7:
                            keyboard.press(Key.right)
                            time.sleep(0.1)
                            keyboard.release(Key.right)
                        elif x > 0.82:
                            keyboard.press(Key.left)
                            time.sleep(0.1)
                            keyboard.release(Key.left)
                        # Once we are "at the bench", we sit
                        else:
                            keyboard.press(Key.up)
                            time.sleep(0.1)
                            keyboard.release(Key.up)
                            time.sleep(0.5)
                            behaviour = "tavern_exit"

            except Exception as e:
                print(e)
                pass

    print("Finished!!!")

    # Clean up the listener
    listener.stop()
    listener.join()


if __name__ == "__main__":
    print("[dim]Waiting 10 seconds before starting...[/dim]")
    time.sleep(10)
    farm(1)
