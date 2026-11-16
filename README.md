# macro
An extension of micro that adds for loops, maps, and closures.

## Editor Support
There exists support for macro in the following editors:
- [VSCode](https://github.com/las-r/macro-vscode)

## Usage
```
python -m macro <file.mic>
```

## Additions
### For loops
```
for V, A
    ...
end
```
`A` is evaluated once and must be an array. Anything else (including a map) raises a `TypeError`. To loop over a map, use `for k, keys(m)` or `for v, vals(m)`.

`V` is assigned each element in turn. It lives in the current scope, so it is still set after the loop ends (to the last element).

### Maps
```
m = {"a" = 1, "b" = 2}
m:"c" = 3
print(m:"a")
```
Maps use the same `:` index syntax as arrays, for both reading and assignment. Reading a missing key is an error.

`keys(m)` returns an array of the keys and `vals(m)` returns an array of the values, both in insertion order.

### Closures
```
add = @(a, b) return a + b end
print(add(1, 2))

func make_adder(n)
    return @(x) return x + n end
end
add5 = make_adder(5)
print(add5(10))
```
`@(params) ... end` is an expression that produces a function value. The parentheses may be left off if there are no parameters.