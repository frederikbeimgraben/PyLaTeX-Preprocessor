"""Package collection and dependency/conflict resolution for documents."""

from ..model.base_model import Package, TeX


def collect_packages(node: TeX) -> set[Package | str]:
    """Recursively collect all required packages from a TeX tree."""
    packages = set(node.required_packages)
    for child in node.children:
        packages.update(collect_packages(child))
    return packages


def resolve_package_dependencies(packages: set[Package | str]) -> set[str]:
    """Resolve package dependencies and return final set of package names.

    Args:
        packages: Set of packages (Package objects or strings)

    Returns:
        Set of package name strings with dependencies resolved

    Raises:
        ValueError: If package conflicts are detected
    """
    result: set[str] = set()
    package_objects: dict[str, Package] = {}

    # Separate Package objects from strings
    for pkg in packages:
        if isinstance(pkg, Package):
            package_objects[pkg.name] = pkg
            result.add(pkg.name)
        else:
            result.add(pkg)

    # Check for conflicts
    for pkg_obj in package_objects.values():
        for conflict in pkg_obj.conflicts:
            conflict_name = conflict if isinstance(conflict, str) else conflict.name
            if conflict_name in result:
                raise ValueError(
                    f"Package conflict: {pkg_obj.name} conflicts with {conflict_name}"
                )

    # Add required dependencies
    for pkg_obj in package_objects.values():
        for required in pkg_obj.requires:
            required_name = required if isinstance(required, str) else required.name
            result.add(required_name)

    return result
