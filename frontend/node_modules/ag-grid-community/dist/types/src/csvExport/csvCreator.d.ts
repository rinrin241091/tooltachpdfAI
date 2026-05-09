import type { NamedBean } from '../context/bean';
import { BaseCreator } from '../export/baseCreator';
import type { CsvCustomContent, CsvExportParams } from '../interfaces/exportParams';
import type { ICsvCreator } from '../interfaces/iCsvCreator';
import { CsvSerializingSession } from './csvSerializingSession';
export declare class CsvCreator extends BaseCreator<CsvCustomContent, CsvSerializingSession, CsvExportParams> implements NamedBean, ICsvCreator {
    beanName: "csvCreator";
    protected getMergedParams(params?: CsvExportParams): CsvExportParams;
    protected export(userParams?: CsvExportParams): void;
    exportDataAsCsv(params?: CsvExportParams): void;
    getDataAsCsv(params?: CsvExportParams, skipDefaultParams?: boolean): string;
    getDefaultFileExtension(): string;
    createSerializingSession(params?: CsvExportParams): CsvSerializingSession;
    isExportSuppressed(): boolean;
}
