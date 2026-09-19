# audio_system.py
import pygame
import math
import random
import array

audio_enabled = False
try:
    if pygame.mixer.get_init():
        audio_enabled = True
    else:
        pygame.mixer.init()
        audio_enabled = bool(pygame.mixer.get_init())
except Exception:
    audio_enabled = False

# 全局音效开关
sound_on = True


def _synth_sound(duration, sr, fn):
    n = int(sr * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / sr
        v = fn(t)
        if v > 1.0:
            v = 1.0
        elif v < -1.0:
            v = -1.0
        s = int(v * 30000)
        buf.append(s)
        buf.append(s)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _make_launch_sound(sr=22050):
    """火箭发射：柔和的上升音。"""
    duration = 0.62
    notes = [523.25, 659.25, 783.99, 1046.5]

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.055
            if t < delay:
                continue
            tt = t - delay
            attack = min(1.0, tt * 45)
            env = math.exp(-tt * 3.2) * attack
            gain = 1.0 / (j * 0.5 + 2.0)
            v += math.sin(2 * math.pi * f * tt) * env * gain * 0.90
            v += math.sin(2 * math.pi * f * 2 * tt) * env * gain * 0.14
        v *= min(1.0, t * 80)
        v *= min(1.0, (duration - t) * 10)
        return v * 0.52

    return _synth_sound(duration, sr, fn)


def _make_explosion_sound(sr=22050):
    """碰撞爆炸：高频冲击 + 低频隆隆。"""
    duration = 0.65
    rnd = random.Random(7)
    n = int(sr * duration)
    high_noise = [rnd.uniform(-1, 1) for _ in range(n)]
    low_noise = []
    prev = 0.0
    for _ in range(n):
        x = rnd.uniform(-1, 1)
        prev += 0.03 * (x - prev)
        low_noise.append(prev * 4.5)

    def fn(t):
        i = int(t * sr)
        if i >= n:
            return 0.0
        high_env = math.exp(-t * 55)
        mid_env = math.exp(-t * 11)
        low_env = math.exp(-t * 3.8)
        v = high_noise[i] * high_env * 0.55
        v += low_noise[i] * mid_env * 0.55
        v += math.sin(2 * math.pi * 42 * t) * low_env * 0.55
        v += math.sin(2 * math.pi * 78 * t) * low_env * 0.28
        v *= min(1.0, t * 400)
        v *= min(1.0, (duration - t) * 14)
        return v * 0.85

    return _synth_sound(duration, sr, fn)


def _make_star_lost_sound(sr=22050):
    duration = 0.40

    def fn(t):
        f = 1200 - 500 * (t / duration)
        env = math.exp(-t * 6)
        v = math.sin(2 * math.pi * f * t) * env * 0.40
        v += math.sin(2 * math.pi * f * 1.5 * t) * env * 0.10
        v *= min(1.0, t * 200)
        v *= min(1.0, (duration - t) * 20)
        return v

    return _synth_sound(duration, sr, fn)


def _make_click_sound(sr=22050):
    duration = 0.08

    def fn(t):
        env = math.exp(-t * 45)
        v = math.sin(2 * math.pi * 880 * t) * env * 0.5
        v += math.sin(2 * math.pi * 1320 * t) * env * 0.3
        v *= min(1.0, t * 400)
        return v

    return _synth_sound(duration, sr, fn)


def _make_win_sound(sr=22050):
    duration = 0.9
    notes = [523.25, 659.25, 783.99, 1046.5]

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.12
            if t < delay:
                continue
            tt = t - delay
            env = math.exp(-tt * 3.5)
            v += math.sin(2 * math.pi * f * tt) * env * 0.22
            v += math.sin(2 * math.pi * f * 2 * tt) * env * 0.08
        v *= min(1.0, t * 100)
        v *= min(1.0, (duration - t) * 10)
        return v

    return _synth_sound(duration, sr, fn)


def _make_fail_sound(sr=22050):
    duration = 0.85
    notes = [392.0, 349.23, 293.66, 220.0]

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.13
            if t < delay:
                continue
            tt = t - delay
            env = math.exp(-tt * 3.0)
            v += math.sin(2 * math.pi * f * tt) * env * 0.25
        v *= min(1.0, t * 100)
        v *= min(1.0, (duration - t) * 8)
        return v

    return _synth_sound(duration, sr, fn)


sfx_launch = None
sfx_explosion = None
sfx_star_lost = None
sfx_click = None
sfx_win = None
sfx_fail = None

if audio_enabled:
    try:
        sfx_launch = _make_launch_sound()
        sfx_explosion = _make_explosion_sound()
        sfx_star_lost = _make_star_lost_sound()
        sfx_click = _make_click_sound()
        sfx_win = _make_win_sound()
        sfx_fail = _make_fail_sound()

        sfx_launch.set_volume(0.50)
        sfx_explosion.set_volume(0.65)
        sfx_star_lost.set_volume(0.42)
        sfx_click.set_volume(0.40)
        sfx_win.set_volume(0.55)
        sfx_fail.set_volume(0.50)
    except Exception:
        audio_enabled = False


def play_sound(sfx):
    if not sound_on:
        return
    if audio_enabled and sfx is not None:
        try:
            sfx.play()
        except Exception:
            pass


def play_launch(): play_sound(sfx_launch)
def play_explosion(): play_sound(sfx_explosion)
def play_star_lost(): play_sound(sfx_star_lost)
def play_click(): play_sound(sfx_click)
def play_win(): play_sound(sfx_win)
def play_fail(): play_sound(sfx_fail)


def toggle_sound():
    global sound_on
    sound_on = not sound_on
    return sound_on
