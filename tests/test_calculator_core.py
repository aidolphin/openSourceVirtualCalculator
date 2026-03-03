import unittest

from hand_calculator_v2 import (
    apply_button,
    safe_eval_expression,
    update_hover_dwell_state,
)


class TestExpressionEngine(unittest.TestCase):
    def test_safe_eval_arithmetic(self):
        self.assertEqual(safe_eval_expression("2+3*4"), 14)
        self.assertEqual(safe_eval_expression("(10-2)/4"), 2.0)
        self.assertEqual(safe_eval_expression("2**3 + 1"), 9)

    def test_safe_eval_functions_and_constants(self):
        self.assertEqual(safe_eval_expression("sqrt(9)"), 3.0)
        self.assertEqual(round(safe_eval_expression("sin(pi/2)"), 6), 1.0)
        self.assertEqual(safe_eval_expression("log(100)"), 2.0)

    def test_safe_eval_blocks_unsafe_names(self):
        with self.assertRaises(Exception):
            safe_eval_expression("__import__('os').system('echo hacked')")
        with self.assertRaises(Exception):
            safe_eval_expression("open('x.txt','w')")


class TestButtonActions(unittest.TestCase):
    def test_apply_button_regular_and_delete_clear(self):
        eq = ""
        eq = apply_button(eq, "1")
        eq = apply_button(eq, "+")
        eq = apply_button(eq, "2")
        self.assertEqual(eq, "1+2")

        eq = apply_button(eq, "DEL")
        self.assertEqual(eq, "1+")

        eq = apply_button(eq, "C")
        self.assertEqual(eq, "")

    def test_apply_button_equals_and_error(self):
        self.assertEqual(apply_button("1+2", "="), "3")
        self.assertEqual(apply_button("1+", "="), "Error")


class TestHoverDwellRegression(unittest.TestCase):
    def test_press_after_dwell_on_same_key(self):
        button = object()
        current_button = None
        hover_elapsed = 0.0
        last_seen_on_key_ts = 0.0
        last_press_ts = 0.0

        for now in (1.0, 1.3, 1.6):
            (
                current_button,
                hover_elapsed,
                last_seen_on_key_ts,
                last_press_ts,
                pressed_button,
            ) = update_hover_dwell_state(
                voted_button=button,
                current_button=current_button,
                hover_elapsed=hover_elapsed,
                last_seen_on_key_ts=last_seen_on_key_ts,
                now=now,
                dt=0.3,
                last_press_ts=last_press_ts,
                dwell_time_required=0.8,
                press_cooldown=0.2,
                hover_grace=0.2,
            )

        self.assertIs(pressed_button, button)
        self.assertEqual(hover_elapsed, 0.0)

    def test_grace_keeps_current_key_briefly(self):
        button = object()
        (
            current_button,
            hover_elapsed,
            last_seen_on_key_ts,
            last_press_ts,
            _,
        ) = update_hover_dwell_state(
            voted_button=button,
            current_button=None,
            hover_elapsed=0.0,
            last_seen_on_key_ts=0.0,
            now=2.0,
            dt=0.2,
            last_press_ts=0.0,
            dwell_time_required=1.0,
            press_cooldown=0.5,
            hover_grace=0.3,
        )

        (
            current_button,
            hover_elapsed,
            _,
            _,
            _,
        ) = update_hover_dwell_state(
            voted_button=None,
            current_button=current_button,
            hover_elapsed=hover_elapsed,
            last_seen_on_key_ts=last_seen_on_key_ts,
            now=2.2,
            dt=0.0,
            last_press_ts=last_press_ts,
            dwell_time_required=1.0,
            press_cooldown=0.5,
            hover_grace=0.3,
        )

        self.assertIs(current_button, button)
        self.assertGreater(hover_elapsed, 0.0)

    def test_off_key_beyond_grace_resets(self):
        button = object()
        (
            current_button,
            hover_elapsed,
            last_seen_on_key_ts,
            last_press_ts,
            _,
        ) = update_hover_dwell_state(
            voted_button=button,
            current_button=None,
            hover_elapsed=0.0,
            last_seen_on_key_ts=0.0,
            now=5.0,
            dt=0.2,
            last_press_ts=0.0,
            dwell_time_required=1.0,
            press_cooldown=0.5,
            hover_grace=0.2,
        )

        (
            current_button,
            hover_elapsed,
            _,
            _,
            _,
        ) = update_hover_dwell_state(
            voted_button=None,
            current_button=current_button,
            hover_elapsed=hover_elapsed,
            last_seen_on_key_ts=last_seen_on_key_ts,
            now=5.5,
            dt=0.0,
            last_press_ts=last_press_ts,
            dwell_time_required=1.0,
            press_cooldown=0.5,
            hover_grace=0.2,
        )

        self.assertIsNone(current_button)
        self.assertEqual(hover_elapsed, 0.0)

    def test_cooldown_blocks_immediate_repress(self):
        button = object()
        current_button = None
        hover_elapsed = 0.0
        last_seen_on_key_ts = 0.0
        last_press_ts = 0.0

        # First press
        (
            current_button,
            hover_elapsed,
            last_seen_on_key_ts,
            last_press_ts,
            pressed_button,
        ) = update_hover_dwell_state(
            voted_button=button,
            current_button=current_button,
            hover_elapsed=hover_elapsed,
            last_seen_on_key_ts=last_seen_on_key_ts,
            now=10.0,
            dt=1.0,
            last_press_ts=last_press_ts,
            dwell_time_required=0.8,
            press_cooldown=0.5,
            hover_grace=0.2,
        )
        self.assertIs(pressed_button, button)

        # Still in cooldown, should not press
        (
            current_button,
            hover_elapsed,
            last_seen_on_key_ts,
            last_press_ts,
            pressed_button,
        ) = update_hover_dwell_state(
            voted_button=button,
            current_button=current_button,
            hover_elapsed=hover_elapsed,
            last_seen_on_key_ts=last_seen_on_key_ts,
            now=10.2,
            dt=1.0,
            last_press_ts=last_press_ts,
            dwell_time_required=0.8,
            press_cooldown=0.5,
            hover_grace=0.2,
        )
        self.assertIsNone(pressed_button)


if __name__ == "__main__":
    unittest.main()
