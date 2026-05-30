"""Tests for the pytex_tikz module."""

from pytex_tikz import (
    Arc,
    Circle,
    Coordinate,
    CoordinateNode,
    CurveTo,
    Cycle,
    Draw,
    EdgeOp,
    Ellipse,
    Fill,
    FillDraw,
    ForEach,
    HorizontalLineTo,
    LineTo,
    MoveTo,
    Node,
    NodeOp,
    Path,
    PathOp,
    PgfMathSetMacro,
    Rectangle,
    Scope,
    Shade,
    TikzPicture,
    TikzSet,
    ToOp,
    UseTikzLibrary,
    VerticalLineTo,
    unroll,
)


class TestCoordinate:
    def test_cartesian(self):
        assert Coordinate.cartesian(1, 2).serialize() == "(1,2)"

    def test_polar(self):
        assert Coordinate.polar(45, "1cm").serialize() == "(45:1cm)"

    def test_named(self):
        assert Coordinate.named("a").serialize() == "(a)"

    def test_named_anchor(self):
        assert Coordinate.named("a", "east").serialize() == "(a.east)"

    def test_relative(self):
        assert Coordinate.relative(1, 2).serialize() == "(++(1,2))"

    def test_relative_single_plus(self):
        assert Coordinate.relative(1, 2, kind="+").serialize() == "(+(1,2))"

    def test_page(self):
        assert (
            Coordinate.page("south east").serialize()
            == "(current page.south east)"
        )


class TestPathOps:
    def test_line_to(self):
        assert LineTo(Coordinate.cartesian(1, 0)).serialize() == "-- (1,0)"

    def test_move_to(self):
        assert MoveTo(Coordinate.cartesian(0, 0)).serialize() == "(0,0)"

    def test_horizontal_line_to(self):
        assert HorizontalLineTo(Coordinate.cartesian(1, 0)).serialize() == "-| (1,0)"

    def test_vertical_line_to(self):
        assert VerticalLineTo(Coordinate.cartesian(1, 0)).serialize() == "|- (1,0)"

    def test_curve_to_two_controls(self):
        out = CurveTo(
            Coordinate.cartesian(1, 1),
            controls=(Coordinate.cartesian(0.3, 0), Coordinate.cartesian(0.7, 1)),
        ).serialize()
        assert out == ".. controls (0.3,0) and (0.7,1) .. (1,1)"

    def test_curve_to_one_control(self):
        out = CurveTo(
            Coordinate.cartesian(1, 1),
            controls=(Coordinate.cartesian(0.5, 0.5),),
        ).serialize()
        assert out == ".. controls (0.5,0.5) .. (1,1)"

    def test_curve_to_no_controls(self):
        assert CurveTo(Coordinate.cartesian(1, 1)).serialize() == ".. (1,1)"

    def test_rectangle(self):
        assert Rectangle(Coordinate.cartesian(2, 1)).serialize() == "rectangle (2,1)"

    def test_circle(self):
        assert Circle("1cm").serialize() == "circle (1cm)"

    def test_ellipse(self):
        assert Ellipse("2cm", "1cm").serialize() == "ellipse (2cm and 1cm)"

    def test_arc(self):
        assert Arc(0, 90, "1cm").serialize() == "arc (0:90:1cm)"

    def test_cycle(self):
        assert Cycle().serialize() == "-- cycle"

    def test_node_op(self):
        out = NodeOp("label", options="above", name="A", at=Coordinate.cartesian(1, 0))
        assert out.serialize() == "node[above] (A) at (1,0) {label}"

    def test_edge_op(self):
        assert EdgeOp(Coordinate.named("B")).serialize() == "edge (B)"

    def test_to_op(self):
        assert ToOp(Coordinate.named("B"), options="bend left").serialize() == \
            "to[bend left] (B)"


class TestPath:
    def test_path_no_options(self):
        out = Path(
            MoveTo(Coordinate.cartesian(0, 0)),
            LineTo(Coordinate.cartesian(1, 1)),
        ).serialize()
        assert out == "\\path (0,0) -- (1,1);"

    def test_draw(self):
        out = Draw(
            MoveTo(Coordinate.cartesian(0, 0)),
            LineTo(Coordinate.cartesian(2, 1)),
            options="thick, blue",
        ).serialize()
        assert out == "\\draw[thick, blue] (0,0) -- (2,1);"

    def test_fill(self):
        out = Fill(
            Coordinate.cartesian(0, 0),
            Circle("0.5cm"),
            options="red!50",
        ).serialize()
        assert out == "\\fill[red!50] (0,0) circle (0.5cm);"

    def test_filldraw(self):
        out = FillDraw(
            Coordinate.cartesian(0, 0),
            Rectangle(Coordinate.cartesian(1, 1)),
            options="fill=blue!10",
        ).serialize()
        assert out == "\\filldraw[fill=blue!10] (0,0) rectangle (1,1);"

    def test_shade(self):
        out = Shade(
            Coordinate.cartesian(0, 0),
            Rectangle(Coordinate.cartesian(1, 1)),
            options="left color=red, right color=blue",
        ).serialize()
        assert "\\shade[left color=red, right color=blue]" in out

    def test_raw_string_op_passthrough(self):
        out = Path(PathOp("(0,0) -- (1,1)")).serialize()
        assert out == "\\path (0,0) -- (1,1);"

    def test_string_op_passthrough(self):
        out = Path("(0,0) -- (1,1)").serialize()
        assert out == "\\path (0,0) -- (1,1);"

    def test_coordinate_op(self):
        out = Path(Coordinate.cartesian(0, 0), LineTo(Coordinate.cartesian(1, 1))).serialize()
        assert out == "\\path (0,0) -- (1,1);"

    def test_packages(self):
        assert "tikz" in Draw(MoveTo(Coordinate.cartesian(0, 0))).required_packages


class TestNode:
    def test_node_minimal(self):
        assert Node("hi").serialize() == "\\node {hi};"

    def test_node_full(self):
        out = Node(
            "lbl",
            options="anchor=north",
            name="A",
            at=Coordinate.cartesian(1, 2),
        ).serialize()
        assert out == "\\node[anchor=north] (A) at (1,2) {lbl};"

    def test_coordinate_node(self):
        out = CoordinateNode("X", at=Coordinate.cartesian(1, 2)).serialize()
        assert out == "\\coordinate (X) at (1,2);"

    def test_coordinate_node_no_at(self):
        assert CoordinateNode("X").serialize() == "\\coordinate (X);"


class TestEnvironments:
    def test_tikzpicture(self):
        out = TikzPicture(
            Draw(MoveTo(Coordinate.cartesian(0, 0)), LineTo(Coordinate.cartesian(1, 1)))
        ).serialize()
        assert out.startswith("\\begin{tikzpicture}\n")
        assert out.endswith("\\end{tikzpicture}")
        assert "\\draw (0,0) -- (1,1);" in out

    def test_tikzpicture_options(self):
        out = TikzPicture(Node("x"), options="overlay, remember picture").serialize()
        assert out.startswith("\\begin{tikzpicture}[overlay, remember picture]\n")

    def test_tikzpicture_multibody(self):
        out = TikzPicture(Node("a"), Node("b")).serialize()
        assert "\\node {a};" in out and "\\node {b};" in out

    def test_scope(self):
        out = Scope(Draw(MoveTo(Coordinate.cartesian(0, 0))), options="rotate=30").serialize()
        assert out.startswith("\\begin{scope}[rotate=30]\n")
        assert out.endswith("\\end{scope}")


class TestPreambleCommands:
    def test_tikzset(self):
        assert TikzSet("every node/.style={draw}").serialize() == \
            "\\tikzset{every node/.style={draw}}"

    def test_use_tikz_library(self):
        out = UseTikzLibrary("arrows.meta", "calc", "positioning").serialize()
        assert out == "\\usetikzlibrary{arrows.meta,calc,positioning}"

    def test_pgfmathsetmacro(self):
        out = PgfMathSetMacro("result", "2*3+1").serialize()
        assert out == "\\pgfmathsetmacro{\\result}{2*3+1}"


class TestForeach:
    def test_unroll(self):
        out = unroll(
            [1, 2, 3],
            lambda i: Node(f"item{i}", at=Coordinate.cartesian(i, 0), name=f"n{i}"),
        ).serialize()
        for i in (1, 2, 3):
            assert f"\\node (n{i}) at ({i},0) {{item{i}}};" in out

    def test_foreach_class(self):
        out = ForEach(
            range(3),
            lambda i: Node(f"x={i}"),
        ).serialize()
        assert out.count("\\node {x=") == 3
