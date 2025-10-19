import os
import time
from typing import Literal

import mss
import numpy as np
from pynput.keyboard import Controller, Key, Listener

from silksong_rosary_farmer.image import (
    color_2_room_is_loading,
    img_2_color_centroid,
    img_2_coloravg,
)
from silksong_rosary_farmer.utils import hex_to_rgb

# Conf
color_hornet_dress = "#ae3446"
max_time_in_minutes = 999_999  #  Effectively no limit btw


# fmt: off
should_stop = False
def on_press(key):
    global keyboard
    if key == Key.esc:
        print("\n🛑 Esc detected - stopping...")
        # Release all keys that might be pressed
        try:
            keyboard.release(Key.right)
            keyboard.release(Key.left)
            keyboard.release(Key.up)
            keyboard.release("c")
            keyboard.release("x")
            keyboard.release("z")
        except:  # noqa: E722
            pass
        os._exit(0)
listener = Listener(on_press=on_press)
listener.start()
print("🎮 Press Esc to stop the script")
print("[dim]Waiting 10 seconds before starting...[/dim]")
time.sleep(10)
# fmt: on


location_prev = "none"
last_location = ""
cooldown_update = time.time()
cooldown_timer = 1
behaviour = "tavern_exit"


def color_2_room(
    color: tuple[float, float, float, float],
) -> Literal["tavern", "exterior", "cave"]:
    """Analyze room type based on RGB color values"""
    global cooldown_update
    global last_location
    global location_prev

    r, g, b, w = color

    # If both green and red are greater than blue, return "tavern"
    if g > b and r > b:
        location_prev = last_location
        last_location = "tavern"
        # print("tavern")
        return "tavern"

    else:
        if last_location == "":
            last_location = "cave"
            # print("tavern")
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


# Pre
keyboard = Controller()
color_rgb = hex_to_rgb(color_hornet_dress)
tolerance = 20
start_time = time.time()
time_last_room_change = time.time()
prev_room_type = "none"


# Loop
with mss.mss() as sct:
    monitor = sct.monitors[1]
    # for _ in range(50):
    while True:
        if should_stop:
            break
        if time.time() - start_time > max_time_in_minutes * 60:
            print("Max time reached!")
            break

        try:
            # 🍑 Screenshot
            screenshot = sct.grab(monitor)
            w, h = screenshot.width, screenshot.height
            img_bgra = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(h, w, 4)
            img_scaled = img_bgra[::2, ::2, [2, 1, 0]]

            # Set the top-left square of the image to black
            img_scaled[
                0 : int(img_scaled.shape[0] * 0.21),
                0 : int(img_scaled.shape[1] * 0.3),
                :,
            ] = 0

            # plt.figure(figsize=(12, 8))
            # plt.imshow(img_scaled)
            # plt.axis("off")
            # plt.title("Right Monitor Screenshot (50% scaled, NEAREST interpolation)")
            # plt.tight_layout()
            # plt.show()

            # 🍑 Room
            avg_color = img_2_coloravg(img_scaled)
            # print(f"W color: {avg_color[-1]}")
            # continue
            room_type = color_2_room(avg_color)
            if room_type != prev_room_type:
                time_last_room_change = time.time()
                prev_room_type = room_type
            print(f"Beh {behaviour} Room: {room_type} Room prev: {location_prev}")

            # 🍑 Behhaviour control
            if behaviour == "tavern_exit" and room_type == "exterior":
                behaviour = "exterior_go_cave"
            if behaviour == "exterior_go_cave" and room_type == "cave":
                behaviour = "cave_fight"
            if behaviour == "cave_go_exterior" and room_type == "exterior":
                print("exterior_go_tavern")
                behaviour = "exterior_go_tavern"
            if behaviour == "exterior_go_tavern" and room_type == "tavern":
                print("tavern_go_bench 0")
                behaviour = "tavern_go_bench"
            if behaviour == "cave_go_exterior" and room_type == "tavern":
                print("tavern_go_bench 1")
                behaviour = "tavern_go_bench"
            if behaviour == "tavern_go_bench" and room_type == "exterior":
                behaviour = "exterior_go_tavern"
            if (
                behaviour in ["tavern_exit", "exterior_go_cave"]
                and (time.time() - time_last_room_change) > 60
            ):
                # Sometimes hornet gets fucking stuck at the rihg end of the cave
                print("")
                print("")
                print("I think... hornet is stuck at the right end of the cave?")
                print("")
                print("")
                behaviour = "cave_go_exterior"
                last_location = "cave"
                room_type = "cave"

            # 🍑 Beh
            if behaviour == "exterior_go_cave":
                keyboard.press(Key.right)
                time.sleep(0.1)
                keyboard.press("c")
                time.sleep(0.5)
                keyboard.release("c")
                time.sleep(0.3)
                keyboard.release(Key.right)

            # 🍑 Beh
            elif behaviour == "exterior_go_tavern":
                keyboard.press(Key.left)
                time.sleep(0.2)
                keyboard.press("c")
                time.sleep(0.4)
                keyboard.release("c")
                time.sleep(0.3)
                keyboard.release(Key.left)

            # 🍑 Beh
            elif behaviour == "cave_fight":
                keyboard.press(Key.right)
                time.sleep(0.2)
                keyboard.press("c")
                time.sleep(1.4)
                keyboard.release("c")
                keyboard.release(Key.right)
                time.sleep(0.1)

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

            # 🍑 Beh
            elif behaviour == "cave_go_exterior":
                # keyboard.press(Key.left)
                # time.sleep(0.2)
                # keyboard.press("c")
                # time.sleep(0.5)
                # keyboard.press("z")
                # time.sleep(0.1)
                # keyboard.release("z")
                # time.sleep(1.5)
                # keyboard.release("c")
                # keyboard.release(Key.left)

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
            result = img_2_color_centroid(img_scaled, color_rgb, tolerance)
            if not result:
                # if room_type != "tavern" and location_prev == "none":
                #     behaviour = "cave_go_exterior"
                #     continue

                # To get away from the fire in the middle of the tavern
                keyboard.press(Key.right)
                time.sleep(0.3)
                keyboard.release(Key.right)
                continue
            x, y = result
            print(f"Coords: x={x:.4f}, y={y:.4f}")

            # print(
            # c     f"Behaviour: {behaviour} Room type: {room_type} | Previous: {location_prev}"
            # )

            # 🍑 Beh
            if behaviour == "tavern_exit":
                if y >= 0.7:  # On the floor
                    # keyboard.press(Key.right)
                    # time.sleep(0.1)
                    # keyboard.release(Key.right)
                    keyboard.press(Key.right)
                    time.sleep(0.2)
                    keyboard.press("c")
                    time.sleep(0.6)
                    keyboard.release("c")
                    keyboard.release(Key.right)
                elif y >= 0.45:  # On the bench slab
                    # keyboard.press(Key.left)
                    # time.sleep(0.1)
                    # keyboard.release(Key.left)
                    keyboard.press(Key.left)
                    time.sleep(0.1)
                    keyboard.release(Key.left)
                    keyboard.press(Key.left)
                    time.sleep(0.2)
                    keyboard.press("c")
                    time.sleep(0.5)
                    keyboard.release("c")
                    keyboard.release(Key.left)

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
                    if x < 0.72:
                        keyboard.press(Key.right)
                        time.sleep(0.1)
                        keyboard.release(Key.right)
                    elif x > 0.75:
                        keyboard.press(Key.left)
                        time.sleep(0.1)
                        keyboard.release(Key.left)
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

                elif y >= 0.45:  # On the bench slab
                    if x < 0.7:
                        keyboard.press(Key.right)
                        time.sleep(0.1)
                        keyboard.release(Key.right)
                    elif x > 0.82:
                        keyboard.press(Key.left)
                        time.sleep(0.1)
                        keyboard.release(Key.left)
                    else:
                        keyboard.press(Key.up)
                        time.sleep(0.1)
                        keyboard.release(Key.up)

                        time.sleep(0.5)
                        behaviour = "tavern_exit"

            # else:
            #     msg = f"Unknown behaviour: {behaviour}"
            #     raise ValueError(msg)

        except Exception as e:
            print(e)
            pass

print("Finished!!!")

# Clean up the listener
print("Cleaning up...")
listener.stop()
listener.join()
