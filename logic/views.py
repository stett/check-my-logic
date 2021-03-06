from django.shortcuts import render
from logic.expression import ExpressionTree


def home(request):

    context = {}
    expression = request.GET.get('expression', None)
    if expression:
        context.update({'original': expression})
        try:
            tree = ExpressionTree(expression)
            context.update({
                'expression': tree.stringify(),
                'tautology': tree.is_tautology(),
                'truth_table': tree.get_truth_table(),
                'tree': tree,
            })
        except Exception as e:
            context.update({
                'error': e
            })

    return render(request, 'home.html', context)
