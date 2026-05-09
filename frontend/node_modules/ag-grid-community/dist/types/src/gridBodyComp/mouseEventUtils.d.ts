import type { BeanCollection } from '../context/context';
import type { GridOptionsService } from '../gridOptionsService';
import type { CellPosition } from '../interfaces/iCellPosition';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getCellPositionForEvent(gos: GridOptionsService, event: MouseEvent | KeyboardEvent | Touch): CellPosition | null;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getNormalisedMousePosition(beans: BeanCollection, event: MouseEvent | {
    x: number;
    y: number;
}): {
    x: number;
    y: number;
};
