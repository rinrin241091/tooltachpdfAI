import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class ExpressionService extends BeanStub implements NamedBean {
    beanName: "expressionSvc";
    private readonly cache;
    evaluate(expression: string | undefined, params: any): any;
    private evaluateExpression;
    private createExpressionFunction;
    private createFunctionBody;
}
