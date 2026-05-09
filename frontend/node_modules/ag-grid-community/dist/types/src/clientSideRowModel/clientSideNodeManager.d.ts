import { BeanStub } from '../context/beanStub';
import { RowNode } from '../entities/rowNode';
import type { RefreshModelParams } from '../interfaces/iClientSideRowModel';
import type { RowDataTransaction } from '../interfaces/rowDataTransaction';
import type { RowNodeTransaction } from '../interfaces/rowNodeTransaction';
import type { ChangedRowNodes } from './changedRowNodes';
export declare class ClientSideNodeManager<TData = any> extends BeanStub {
    readonly rootNode: RowNode<TData>;
    private nextId;
    private allNodesMap;
    constructor(rootNode: RowNode<TData>);
    getRowNode(id: string): RowNode | undefined;
    setNewRowData(rowData: TData[]): void;
    private destroyAllNodes;
    setImmutableRowData(params: RefreshModelParams<TData>, rowData: TData[]): void;
    private deleteUnusedNodes;
    updateRowData(rowDataTran: RowDataTransaction<TData>, changedRowNodes: ChangedRowNodes<TData>, animate: boolean): RowNodeTransaction<TData>;
    private executeRemove;
    private executeUpdate;
    private executeAdd;
    private dispatchRowDataUpdateStarted;
    private deselect;
    private createRowNode;
    /** Called when a node needs to be deleted */
    private destroyNode;
    private lookupNode;
    private sanitizeAddIndex;
}
