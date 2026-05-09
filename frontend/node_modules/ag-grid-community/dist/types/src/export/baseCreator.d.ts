import { BeanStub } from '../context/beanStub';
import type { ExportParams } from '../interfaces/exportParams';
import type { GridSerializingSession } from './iGridSerializer';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare abstract class BaseCreator<T, S extends GridSerializingSession<T>, P extends ExportParams<T>> extends BeanStub {
    protected abstract export(userParams?: P, compress?: boolean): void;
    protected abstract getMergedParams(params?: P): P;
    protected getFileName(fileName?: string): string;
    protected getData(params: P): string;
    getDefaultFileName(): string;
    abstract createSerializingSession(params?: P): S;
    abstract getDefaultFileExtension(): string;
    abstract isExportSuppressed(): boolean;
}
