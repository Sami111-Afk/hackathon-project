import { Composition } from 'remotion'
import { ORB, TOTAL_FRAMES, FPS } from './ORB'

export const Root = () => (
  <Composition id="ORB" component={ORB} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />
)
