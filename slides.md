---
title: Proc Macros
separator: <!--s-->
verticalSeparator: <!--v-->
theme: black
highlightTheme: ir-black
revealOptions:
  transition: 'fade'
---

# Proc Macros

Let's make writing Rust proc-macro fun

##### Presented by Dan Aloni ([@DanAloni](https://twitter.com/DanAloni))

https://github.com/da-x/rust-gentle-proc-macro

---

## Two main types of Rust macros

Declarative: using pattern matching

```rust
macro_rules! hello {
    (3) => {
        println!("three!");
    };
    ($e:expr) => {
        $e;
    };
}
```

Procedural: compiled using Rust code

```rust
#[proc_macro]
pub fn hello(_: TokenStream) -> TokenStream {
    panic!("Help! I'm scared implementing this");
}
```
