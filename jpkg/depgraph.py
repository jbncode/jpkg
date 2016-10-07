def topological_sort(objects, dependencies):
    # Performs a topological sort (using the depth-first search algorithm).
    # objects: List of strings.
    # dependencies: List of lists of strings, order matching objects so that
    #               dependencies[i] is a list of the dependencies of objects[i].
    # Returns the objects in the order they should be built.
    marks_permanent = [False for i in objects]
    marks_temp = [False for i in objects]
    sorted_list = []

    while False in marks_permanent:
        for idx in range(len(marks_permanent)):
            if not marks_permanent[idx]:
                toposort_visit(idx, objects, dependencies, marks_permanent,
                        marks_temp, sorted_list)

    return sorted_list


def toposort_visit(idx, objects, dependencies, marks_permanent, marks_temp,
        sorted_list):
    if marks_temp[idx]:
        raise Exception("not a directed acyclic graph, cannot be topologically sorted.")
    if not marks_permanent[idx]:
        marks_temp[idx] = True
        for other_name in dependencies[idx]:
            toposort_visit(objects.index(other_name), objects, dependencies,
                    marks_permanent, marks_temp, sorted_list)
        marks_permanent[idx] = True
        marks_temp[idx] = False
        sorted_list.append(objects[idx])
