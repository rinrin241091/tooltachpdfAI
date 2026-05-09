import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
import type { CellClassParams, ColDef } from '../entities/colDef';
import type { CellCtrl } from '../rendering/cell/cellCtrl';
import { CellCustomStyleFeature } from './cellCustomStyleFeature';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class CellStyleService extends BeanStub implements NamedBean {
    beanName: "cellStyles";
    processAllCellClasses(colDef: ColDef, params: CellClassParams, onApplicableClass: (className: string) => void, onNotApplicableClass?: (className: string) => void): void;
    getStaticCellClasses(colDef: ColDef, params: CellClassParams): string[];
    createCellCustomStyleFeature(ctrl: CellCtrl): CellCustomStyleFeature;
    private processStaticCellClasses;
}
