import { BeanStub } from '../../../context/beanStub';
import type { AgColumn } from '../../../entities/agColumn';
export declare class HeaderCellMouseListenerFeature extends BeanStub {
    private readonly column;
    private readonly eGui;
    private lastMovingChanged;
    constructor(column: AgColumn, eGui: HTMLElement);
    postConstruct(): void;
    onClick(event: MouseEvent): void;
}
