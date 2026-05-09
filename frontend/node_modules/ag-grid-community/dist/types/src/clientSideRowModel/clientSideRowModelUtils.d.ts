import type { RowNode } from '../entities/rowNode';
import type { IRowNode } from '../interfaces/iRowNode';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare const _csrmFirstLeaf: (node: IRowNode) => RowNode | undefined;
/**
 * Reorders the children of the root node, so that the rows to move are in the correct order.
 * @param allLeafs The list of all leaf rows of the root node
 * @param leafsToMove The valid set of rows to move, as returned by getValidRowsToMove
 * @param firstAffectedLeafIdx The first index of the rows to move
 * @param targetPositionIdx The target index, where the rows will be moved
 * @param lastAffectedLeafIndex The last index of the rows to move
 * @returns True if the order of the rows changed, false otherwise
 * @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time.
 */
export declare const _csrmReorderAllLeafs: (allLeafs: RowNode[] | null | undefined, leafsToMove: ReadonlySet<RowNode>, target: IRowNode | null | undefined, above: boolean) => boolean;
