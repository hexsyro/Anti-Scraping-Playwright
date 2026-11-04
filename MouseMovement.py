import random
import time
import math


def ease_in_out(t: float) -> float:
    return t * t * (3 - 2 * t)


def bezier_curve(p0, p1, p2, p3, t):
    return (
        (1 - t) ** 3 * p0[0]
        + 3 * (1 - t) ** 2 * t * p1[0]
        + 3 * (1 - t) * t ** 2 * p2[0]
        + t ** 3 * p3[0],
        (1 - t) ** 3 * p0[1]
        + 3 * (1 - t) ** 2 * t * p1[1]
        + 3 * (1 - t) * t ** 2 * p2[1]
        + t ** 3 * p3[1],
    )


def human_mouse_move(
    page,
    start: tuple,
    end: tuple,
    duration: float | None = None,
):
    if duration is None:
        distance = math.dist(start, end)
        duration = min(max(distance / 800, 0.4), 1.6)

    steps = int(duration * random.randint(90, 140))

    x0, y0 = start
    x1, y1 = end

    cp1 = (
        x0 + random.randint(-120, 120),
        y0 + random.randint(-120, 120),
    )
    cp2 = (
        x1 + random.randint(-120, 120),
        y1 + random.randint(-120, 120),
    )

    for i in range(steps):
        t = ease_in_out(i / steps)
        x, y = bezier_curve((x0, y0), cp1, cp2, (x1, y1), t)

        x += random.uniform(-0.6, 0.6)
        y += random.uniform(-0.6, 0.6)

        page.mouse.move(x, y)
        time.sleep(random.uniform(0.002, 0.009))


def human_click(page, x: float, y: float):
    time.sleep(random.uniform(0.08, 0.25))
    page.mouse.down()
    time.sleep(random.uniform(0.04, 0.12))
    page.mouse.up()


def move_to_element(page, selector: str):
    box = page.locator(selector).bounding_box()
    if not box:
        return

    target_x = box["x"] + box["width"] * random.uniform(0.3, 0.7)
    target_y = box["y"] + box["height"] * random.uniform(0.3, 0.7)

    start_x = random.randint(0, int(box["x"] + 50))
    start_y = random.randint(0, int(box["y"] + 50))

    page.mouse.move(start_x, start_y)
    human_mouse_move(page, (start_x, start_y), (target_x, target_y))
    human_click(page, target_x, target_y)
