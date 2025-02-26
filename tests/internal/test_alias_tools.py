import unittest

from pymoca.backends.casadi.alias_relation import AliasRelation

import rtctools._internal.alias_tools as alias_tools


class AliasToolsTest(unittest.TestCase):
    def setUp(self):
        self.ordered_set = alias_tools.OrderedSet([1, "a", "text"])

        alias_relation = AliasRelation()
        alias_relation.add("a", "b")
        alias_relation.add("x", "-y")
        self.alias_dict = alias_tools.AliasDict(alias_relation)
        self.alias_dict["-a"] = 10
        self.alias_dict["y"] = 20

    def test_create_ordered_set(self):
        """Also tests getitem."""
        self.assertEqual(self.ordered_set[0], 1)
        self.assertEqual(self.ordered_set[1], "a")
        self.assertEqual(self.ordered_set[2], "text")
        self.assertEqual(self.ordered_set, [1, "a", "text"])

    def test_ordered_set_len(self):
        self.assertEqual(len(self.ordered_set), 3)

    def test_ordered_set_contains(self):
        self.assertTrue("text" in self.ordered_set)
        self.assertFalse(2 in self.ordered_set)

    def test_ordered_set_get_state(self):
        state = self.ordered_set.__getstate__()
        self.assertIsInstance(state, list)
        self.assertEqual(state[0], 1)

    def test_ordered_set_set_state(self):
        ordered_set = alias_tools.OrderedSet()
        ordered_set.__setstate__([1, 2, "text"])
        self.assertIsInstance(ordered_set, alias_tools.OrderedSet)
        self.assertEqual(ordered_set[2], "text")

    def test_ordered_set_add(self):
        self.ordered_set.add(10)
        self.assertEqual(self.ordered_set[3], 10)

    def test_ordered_set_discard(self):
        self.ordered_set.discard("a")
        self.assertEqual(self.ordered_set[1], "text")
        self.assertEqual(len(self.ordered_set), 2)

    def test_ordered_set_iter(self):
        values = list(self.ordered_set)
        self.assertIsInstance(values, list)
        self.assertEqual(values, [1, "a", "text"])

    def test_ordered_set_reversed(self):
        values = list(reversed(self.ordered_set))
        self.assertEqual(values, ["text", "a", 1])

    def test_ordered_set_pop(self):
        value = self.ordered_set.pop()
        self.assertEqual(value, "text")
        self.assertEqual(len(self.ordered_set), 2)

    def test_ordered_set_pop_first(self):
        value = self.ordered_set.pop(last=False)
        self.assertEqual(value, 1)
        self.assertEqual(self.ordered_set[1], "text")
        self.assertEqual(len(self.ordered_set), 2)

    def test_ordered_set_eq(self):
        ordered_set_1 = alias_tools.OrderedSet([1, "a", "text"])
        ordered_set_2 = alias_tools.OrderedSet([1, "a", 3])
        self.assertTrue(self.ordered_set == ordered_set_1)
        self.assertFalse(self.ordered_set == ordered_set_2)

    def test_create_alias_dict(self):
        """Also tests canonical_signed, setitem, and getitem."""
        self.assertEqual(self.alias_dict["b"], -10)
        self.assertEqual(self.alias_dict["x"], -20)

    def test_alias_dict_del_item(self):
        del self.alias_dict["b"]
        self.assertEqual(list(self.alias_dict.keys()), ["x"])

    def test_alias_dict_contains(self):
        self.assertTrue("y" in self.alias_dict)
        self.assertTrue("-a" in self.alias_dict)
        self.assertTrue("-b" in self.alias_dict)
        self.assertFalse("z" in self.alias_dict)

    def test_alias_dict_len(self):
        self.assertEqual(len(self.alias_dict), 2)

    def test_alias_dict_iter(self):
        keys = set(self.alias_dict)
        self.assertEqual(keys, {"a", "x"})

    def test_alias_dict_update(self):
        self.alias_dict.update({"-b": -30, "c": 40})
        self.assertEqual(self.alias_dict["a"], 30)
        self.assertEqual(self.alias_dict["x"], -20)
        self.assertEqual(self.alias_dict["c"], 40)

    def test_alias_dict_get(self):
        self.assertEqual(self.alias_dict.get("-b", 0), 10)
        self.assertEqual(self.alias_dict.get("-c", 0), 0)

    def test_alias_dict_set_default(self):
        value = self.alias_dict.setdefault("-y", 100)
        self.assertEqual(value, -20)
        self.assertEqual(self.alias_dict["x"], -20)
        value = self.alias_dict.setdefault("-c", 100)
        self.assertEqual(value, 100)
        self.assertEqual(self.alias_dict["c"], -100)

    def test_alias_dict_keys(self):
        self.assertEqual(set(self.alias_dict.keys()), {"a", "x"})

    def test_alias_dict_values(self):
        self.assertEqual(set(self.alias_dict.values()), {-10, -20})

    def test_alias_dict_items(self):
        keys = []
        values = []
        for key, value in self.alias_dict.items():
            keys.append(key)
            values.append(value)
        self.assertEqual(set(keys), {"a", "x"})
        self.assertEqual(set(values), {-10, -20})

    def test_alias_dict_copy(self):
        alias_dict = self.alias_dict.copy()
        self.assertEqual(alias_dict["-b"], 10)
        self.assertEqual(alias_dict["y"], 20)
