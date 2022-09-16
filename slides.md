---
title: Proc Macros
separator: <!--s-->
verticalSeparator: <!--v-->
theme: black
highlightTheme: ir-black
revealOptions:
  transition: 'fade'
---

# Proc Macros Gently

Let's make writing Rust procedural macros fun

##### Presented by Dan Aloni ([@DanAloni](https://twitter.com/DanAloni))

https://github.com/da-x/rust-gentle-proc-macro

---

## Procedural Macros Topics

- In this talk I'll show:
    - Useful crates to assist in implementation
    - Techniques to handle derive parsing
    - How to provide diagnostics for proc macro users
    - Techniques in debugging proc macros
    - Performance tricks

---

## Two main types of Rust macros

Declarative: using pattern matching

<!--- snippet-name: hello -->
```rust
macro_rules! hello {
    (3) => { println!("three!"); };
    ($e:expr) => { println!("expr: {}", $e); };
}
```

Procedural: compiled Rust code, AKA "proc macro"

<!--- snippet-name: hello-proc -->
<!--- snippet-template: proc-macro -->
```rust
#[proc_macro]
pub fn hello(_: TokenStream) -> TokenStream {
    panic!("Help! I'm scared implementing this");
}
```
---

- Declarative: defined via pattern matching, can be used
inside the same crate that defines it.
- Procedural:
    - Compiled Rust code.
    - Has to be contained in a special `lib` crate.
    - Shared library that `rustc` loads.
    - Can run faster than declarative equivalent.

---

## Types of proc macros

- Function-like:  `call!{}`
- Attribute:  `#[attr]`
- Derive :  `#[Derive(Macro)]`

---

## Cargo.toml: proc macro crates

```toml
[package]
name = "hello"
version = "0.1.0"
edition = "2021"

[lib]
proc-macro = true # Special type of crate

[dependencies]
# For generating Rust code (and token streams in general)
quote = "1.*"
# For parsing Rust code (and token streams in general)
syn = { version = "1.0.*", features = ["full"]  }
proc-macro2 = "1" # Helper
```

---

<!--- snippet-name: hello2 -->
```rust
macro_rules! hello {
    (3) => { println!("three!"); };
    ($e:expr) => { println!("expr: {}", $e); };
}
```

<!--- snippet-name: hello-proc2 -->
<!--- snippet-template: proc-macro2 -->

Re-implemented as a 'function-like' procedural macro:

```rust
use {proc_macro::TokenStream, quote::quote};

#[proc_macro]
pub fn hello(input: TokenStream) -> TokenStream {
    if let Ok(_) = syn::parse::<syn::Lit>(input.clone()) {
        return quote! { println!("three!"); }.into()
    }

    if let Ok(e) = syn::parse::<syn::Expr>(input) {
        return quote! { println!("expr: {}", #e); }.into()
    }

    panic!("nothing matched");
}
```

---

## The `quote` crate

- Provides the `quote` macro that generates a token stream. Supports interpolation of other token
streams or typed AST fragments in a syntax similar to declarative macros.

```rust
let sometype = quote! { Vec<u64> };
quote! { let value: #sometype = vec![]; }
```

```rust
let list_of_stuff = vec![quote!{ 3 }, quote!{ 4 }];
quote! { let value = vec![#(#list_of_stuff),*]; }
```


---

* Using interpolation for composition of several other token stream generated previously by `quote!`:

```rust
let type_definition = quote! {...};
let methods = quote! {...};

let tokens = quote! {
    #type_definition
    #methods
};
```

---

## The `syn` crate

* Industry standard parser for Rust code providing typed AST representation.
* It can also parse non-Rust code from Rust tokens using `Parse` trait impl.

---

## Example: `lazy_static`

```rust
lazy_static! {
    static ref WRD: Regex = Regex::new("[a-z]+").unwrap();
}
```

Let's parse this into:

```
struct LazyStatic {
    visibility: syn::Visibility,
    name: syn::Ident,
    ty: syn::Type,
    init: syn::Expr,
}
```


---

`lazy_static` parsing impl
```rust
impl Parse for LazyStatic {
    fn parse(input: ParseStream) -> Result<Self> {
        let visibility: Visibility = input.parse()?;
        input.parse::<Token![static]>()?;
        input.parse::<Token![ref]>()?;
        let name: Ident = input.parse()?;
        input.parse::<Token![:]>()?;
        let ty: Type = input.parse()?;
        input.parse::<Token![=]>()?;
        let init: Expr = input.parse()?;
        input.parse::<Token![;]>()?;
        Ok(LazyStatic { visibility, name, ty, init })
    }
}
```
---

```rust
#[proc_macro]
pub fn lazy_static(input: TokenStream) -> TokenStream {
    let LazyStatic {
        visibility,
        name,
        ty,
        init,
    } = parse_macro_input!(input as LazyStatic);

    ...
}
```

See the [rest of the example](https://github.com/dtolnay/syn/blob/fa1a855ea02661cf79e7d6af1e60b5a4a08698ac/examples/lazy-static/lazy-static/src/lib.rs) in `syn` repo.

---

### Syn macro `parse_quote!{}`

Like `quote` but outputs concrete AST types rather than token
stream. Assists in generating valid Rust.

```rust
let name = quote!(v);
let ty = quote!(u8);

let stmt: Stmt = parse_quote! {
    let #name: #ty = Default::default();
};
```

---

### Derive macros

* We can implement a macro to be used with `#[derive(..)]`. i.e to be used in the following manner:

```rust
use mymacro::MyMacro;

#[derive(MyMacro)]
struct Foo {
    field: u16,
}
```


---

* Input is the token stream of the type definition, output
  are tokens appended in compilation.
* Name of helper attributes can be specified.

```rust
#[proc_macro_derive(MyMacro, attributes(mymacro))]
pub fn my_macro(input: TokenStream) -> TokenStream {
    // Parse the tokens into a syntax tree
    let ast: DeriveInput = syn::parse(input).unwrap();

    // Build the output
    quote! {
        /* ... */
    }.into();
}
```

---

## `syn`'s DeriveInput

```rust []
pub struct DeriveInput {
    pub attrs: Vec<Attribute>,
    pub vis: Visibility,
    pub ident: Ident,
    pub generics: Generics,
    pub data: Data,
}

pub enum Data {
    Struct(DataStruct),
    Enum(DataEnum),
    Union(DataUnion),
}
```

---

## `syn`'s DeriveInput
```rust [11]
pub struct DeriveInput {
    pub attrs: Vec<Attribute>,
    pub vis: Visibility,
    pub ident: Ident,
    pub generics: Generics,
    pub data: Data,
}

pub enum Data {
    Struct(DataStruct),
    Enum(DataEnum),
    Union(DataUnion),
}
```

---

```rust []
pub struct DataEnum {
    pub enum_token: Enum,
    pub brace_token: Brace,
    pub variants: Punctuated<Variant, Comma>,
}

pub struct Variant {
    pub attrs: Vec<Attribute>,
    pub ident: Ident,
    pub fields: Fields,
    pub discriminant: Option<(Eq, Expr)>,
}
```
---

```rust [4,10]
pub struct DataEnum {
    pub enum_token: Enum,
    pub brace_token: Brace,
    pub variants: Punctuated<Variant, Comma>,
}

pub struct Variant {
    pub attrs: Vec<Attribute>,
    pub ident: Ident,
    pub fields: Fields,
    pub discriminant: Option<(Eq, Expr)>,
}
```

---

```rust []
pub enum Fields {
    Named(FieldsNamed),
    Unnamed(FieldsUnnamed),
    Unit,
}

pub struct FieldsNamed {
    pub brace_token: Brace,
    pub named: Punctuated<Field, Comma>,
}
```

---

```rust [2,9]
pub enum Fields {
    Named(FieldsNamed),
    Unnamed(FieldsUnnamed),
    Unit,
}

pub struct FieldsNamed {
    pub brace_token: Brace,
    pub named: Punctuated<Field, Comma>,
}
```

---

```rust []
pub struct Field {
    pub attrs: Vec<Attribute>,
    pub vis: Visibility,
    pub ident: Option<Ident>,
    pub colon_token: Option<Colon>,
    pub ty: Type,
}
```

---

## Derive macro helper

- [`proc_macro_roids`](https://docs.rs/proc_macro_roids/latest/proc_macro_roids/) crate adds helper methods to `DeriveInput`
and related types.

```rust
let ast = parse_macro_input!(input as DeriveInput);
let relevant_fields = ast.fields()
    .iter()
    .filter(|field| !field.is_phantom_data())
    .filter(|field| !field.contains_tag(
       &parse_quote!(super_derive), &parse_quote!(skip)));

```

---


### Single crate, multiple proc macros

A single proc macro crate can export several macros.

```rust
#[proc_macro]
pub fn foo(_: TokenStream) -> TokenStream {
    ...
}

#[proc_macro]
pub fn bar(_: TokenStream) -> TokenStream {
    ...
}
```

---


## Trick: Export your derive macro

This is only available as `#[derive(Foo)]`:

```rust
#[proc_macro_derive(Foo, attributes(foo))]
pub fn foo(_: TokenStream) -> TokenStream {
    ...
}
```

Re-export this logic as a function-like macro:

```rust
#[proc_macro]
pub fn foo_derive(input: TokenStream) -> TokenStream {
    foo(input)
}
```

---

This way you can execute your derive on `std` types:

```rust
foo_derive!{
    struct Option {
        Some(x),
        None,
    }
}
```

Works on some cases, instead of writing an `impl` for them by hand.


---

## Providing diagnostics

Using `panic!` is discouraged. For example:

```rust [7]
#[proc_macro_derive(MyMacro, attributes(mymacro))]
pub fn foo(input: TokenStream) -> TokenStream {
    let ast: DeriveInput = syn::parse(input).unwrap();
    match ast.data {
        Struct{..} => {}
        Enum{..} => {}
        _ => panic!("no support for this type kind"),
    }

    quote!{ }.into()
}

---

#### Result:
```
error: proc-macro derive panicked
 --> src/main.rs:4:10
  |
4 | #[derive(MyMacro)]
  |          ^^^^^^^
  |
  = help: message: no support for this type kind


---

- Use the `proc_macro_error` crate (see [guide](https://docs.rs/proc-macro-error/1.0.4/proc_macro_error/index.html#guide)).

```rust [2,8-9]
#[proc_macro_derive(MyMacro, attributes(mymacro))]
#[proc_macro_error]
pub fn foo(input: TokenStream) -> TokenStream {
    let ast: DeriveInput = syn::parse(input).unwrap();
    match ast.data {
        Struct{..} => {}
        Enum{..} => {}
        _ => proc_macro_error::abort_call_site!(
            "no support for this type kind"),
    }

    quote!{ }.into()
}
```

---

#### Result:

```
error: no support for this type kind
 --> src/main.rs:4:10
  |
4 | #[derive(MyMacro)]
  |          ^^^^^^^
```
---

We can use pointers to user code, these are `Span`s:

```rust [2,8-11]
#[proc_macro_derive(MyMacro, attributes(mymacro))]
#[proc_macro_error]
pub fn foo(input: TokenStream) -> TokenStream {
    let ast: DeriveInput = syn::parse(input).unwrap();
    match ast.data {
        Struct{..} => {}
        Enum{..} => {}
        _ => proc_macro_error::abort!(
             ast.ident.span(),
                "mymacro: no support for deriving \
                 on this type kind"),
    }
    quote!{ }.into()
}
```

---

#### Result:

```
error: mymacro: no support for deriving on this type kind
 --> src/main.rs:5:7
  |
5 | union Test {
  |       ^^^^
```

---

## Debugging proc macros

* Sometimes during development your proc macro may generate
  a valid `TokenStream` but invalid Rust code.
* Cannot use `cargo expand` in that case.
* The `Display` impl for `TokenStream` and `syn` types are not
  good enough to eyeball the issue.

---

```rust
// Pretty-print generated Rust code via rustfmt
fn rustfmt(code: TokenStream) -> String {
    let out: Option<&mut std::io::Sink> = None;

    let (_, result, _) = rustfmt::format_input(
        rustfmt::Input::Text(format!("{}", code)),
        &Default::default(), out)
        .expect("rustfmt failed");

    format!("{}", result.first()
        .expect("rustfmt returned no code").1)
}
```

---

## TODO

- Attribute macros.
- Hygiene: Use `crate::` in generated code.
- Consider generating a submodule for derive.
- Write about building proc macro in release for dev build.
- Annoying things: go-to definition does not work.
