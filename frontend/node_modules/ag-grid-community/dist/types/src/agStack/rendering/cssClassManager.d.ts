/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class CssClassManager {
    private readonly getGui;
    private cssClassStates;
    constructor(getGui: () => HTMLElement | undefined | null);
    toggleCss(className: string, addOrRemove: boolean): void;
}
