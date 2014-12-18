from django.shortcuts import render
from logic.expression import ExpressionTree


def home(request):

    context = {}
    expression = request.GET.get('expression', None)
    if expression:
        tree = ExpressionTree(expression)
        context.update({
            'original': tree.expression,
            'expression': tree.stringify(),
            'tautology': tree.is_tautology(),
            'truth_table': tree.get_truth_table(),
            'tree': tree,
        })

    return render(request, 'home.html', context)
