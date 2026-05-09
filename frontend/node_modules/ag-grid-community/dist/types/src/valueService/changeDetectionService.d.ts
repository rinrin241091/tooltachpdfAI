import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
export declare class ChangeDetectionService extends BeanStub implements NamedBean {
    beanName: "changeDetectionSvc";
    /**
     * Nesting depth for `beginDeferred`/`endDeferred` calls.
     * Positive while a batch is active; `cellValueChanged` events are accumulated rather than flushed immediately.
     * Using a counter (not a boolean) so nested callers — e.g. `groupRowValueSetter` called from inside
     * a clipboard or fill-handle deferred block — do not prematurely flush the outer batch.
     */
    private deferredDepth;
    /** Accumulated `ChangedPath` for the current batch (CSRM only). `null` until the first CSRM change arrives. */
    private batchedPath;
    /** Nodes queued for direct refresh that are not in the path. */
    private batchedNodes;
    /** Cached CSRM reference, set once in postConstruct. */
    private csrm;
    destroy(): void;
    postConstruct(): void;
    /**
     * Begin a deferred change-detection pass: subsequent `cellValueChanged` events are accumulated
     * rather than triggering individual aggregation + refresh passes. Flush happens on endDeferred().
     * Calls may be nested — flush only occurs when the outermost endDeferred() is reached.
     */
    beginDeferred(): void;
    /**
     * End a deferred pass. When the outermost call is reached (depth returns to zero), runs a single
     * aggregation pass over all accumulated changes and refreshes the affected rows in depth-first order.
     */
    endDeferred(): void;
    private onCellValueChanged;
}
