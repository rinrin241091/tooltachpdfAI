import type { RowNode } from '../entities/rowNode';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class ChangedRowNodes<TData = any> {
    reordered: boolean;
    readonly removals: RowNode<TData>[];
    readonly updates: Set<RowNode<TData>>;
    readonly adds: Set<RowNode<TData>>;
}
